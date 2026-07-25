using LogicLens.Core.Model;
using LogicLens.State;

var tests = new (string Name, Action Test)[]
{
    ("apply, replace, replay, and idempotency", ApplyReplaceReplayAndIdempotency),
    ("semantic no-op receipts", SemanticNoOpReceipts),
    ("normalized retry content", NormalizedRetryContent),
    ("incomplete tail recovery", IncompleteTailRecovery),
    ("durable frame recovery", DurableFrameRecovery),
    ("committed corruption rejection", CommittedCorruptionRejection),
    ("snapshot identity pin", SnapshotIdentityPin),
    ("exclusive writer", ExclusiveWriter),
    ("deterministic journal bytes", DeterministicJournalBytes),
};

foreach (var (name, test) in tests)
{
    test();
    Console.WriteLine($"PASS: {name}");
}

Console.WriteLine("LogicLens runtime state verification passed.");
return;

static void ApplyReplaceReplayAndIdempotency()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var addedFact = CanonicalFact.Create(
        Person,
        EmailPredicate,
        LiteralObject.Plain("alex@example.invalid"));
    var add = new ApplyDeltaCommand(
        "cmd-add-email",
        0,
        "user:sergey",
        add: [new AddFactOperation(
            addedFact.Subject,
            addedFact.Predicate,
            addedFact.Object)]);

    long lengthAfterAdd;
    ApplyDeltaResult accepted;
    using (var store = Open(directory.Path, snapshot))
    {
        accepted = store.ApplyDelta(add);
        Equal(0L, accepted.BeforeRevision, "add before revision");
        Equal(1L, accepted.AfterRevision, "add after revision");
        True(accepted.Changed, "add must change state");
        SequenceEqual(
            [addedFact.FactId],
            accepted.AddedFactIds,
            "added FactIds");
        Equal(1L, store.Revision, "store revision after add");
        True(store.TryGetFact(addedFact.FactId, out var added), "added fact missing");
        var editOrigin = Single(added!.Origins.OfType<EditRuntimeFactOrigin>());
        Equal("cmd-add-email", editOrigin.CommandId, "edit origin command");
        Equal("user:sergey", editOrigin.Actor, "edit origin actor");
        Equal(FixedNow, editOrigin.TimestampUtc, "edit origin timestamp");

        var retry = store.ApplyDelta(add);
        ResultsEqual(accepted, retry, "exact retry");
        lengthAfterAdd = new FileInfo(store.LogPath).Length;

        var conflicting = new ApplyDeltaCommand(
            "cmd-add-email",
            0,
            "user:sergey",
            add: [new AddFactOperation(
                Person,
                EmailPredicate,
                LiteralObject.Plain("other@example.invalid"))]);
        Throws<RuntimeCommandConflictException>(
            () => store.ApplyDelta(conflicting),
            "CommandId reuse must fail");
        Equal(lengthAfterAdd, new FileInfo(store.LogPath).Length, "conflict wrote bytes");

        var stale = new ApplyDeltaCommand(
            "cmd-stale",
            0,
            "user:sergey",
            delete: [new DeleteFactOperation(addedFact.FactId)]);
        Throws<RuntimeRevisionConflictException>(
            () => store.ApplyDelta(stale),
            "stale command must fail");
        False(store.TryGetReceipt("cmd-stale", out _), "stale receipt persisted");
        Equal(lengthAfterAdd, new FileInfo(store.LogPath).Length, "stale command wrote bytes");

        var oldName = snapshot.Facts.Single().Fact;
        var newName = CanonicalFact.Create(
            Person,
            NamePredicate,
            LiteralObject.LanguageTagged("Алексей Ветров", "ru"));
        var replacement = new ApplyDeltaCommand(
            "cmd-replace-name",
            1,
            "user:sergey",
            add: [new AddFactOperation(
                newName.Subject,
                newName.Predicate,
                newName.Object)],
            delete: [new DeleteFactOperation(oldName.FactId)]);
        var replaced = store.ApplyDelta(replacement);
        Equal(2L, replaced.AfterRevision, "replacement revision");
        SequenceEqual([newName.FactId], replaced.AddedFactIds, "replacement add");
        SequenceEqual([oldName.FactId], replaced.DeletedFactIds, "replacement delete");
        False(store.TryGetFact(oldName.FactId, out _), "old name remains active");
        True(store.TryGetFact(newName.FactId, out _), "new name is absent");
    }

    using (var reopened = Open(directory.Path, snapshot))
    {
        Equal(2L, reopened.Revision, "replayed revision");
        True(reopened.TryGetFact(addedFact.FactId, out _), "replayed add missing");
        True(reopened.TryGetReceipt("cmd-add-email", out var receipt), "receipt missing");
        ResultsEqual(accepted, receipt!, "replayed receipt");
        var retryAfterLaterRevision = reopened.ApplyDelta(add);
        ResultsEqual(accepted, retryAfterLaterRevision, "retry after later revision");

        var originalName = snapshot.Facts.Single().Fact;
        var readd = new ApplyDeltaCommand(
            "cmd-readd-original",
            2,
            "user:sergey",
            add: [new AddFactOperation(
                originalName.Subject,
                originalName.Predicate,
                originalName.Object)]);
        var readded = reopened.ApplyDelta(readd);
        Equal(originalName.FactId, Single(readded.AddedFactIds), "re-added FactId changed");
    }
}

static void SemanticNoOpReceipts()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var existing = snapshot.Facts.Single().Fact;
    ApplyDeltaResult result;
    using (var store = Open(directory.Path, snapshot))
    {
        result = store.ApplyDelta(new ApplyDeltaCommand(
            "cmd-no-op",
            0,
            "user:sergey",
            add: [new AddFactOperation(
                existing.Subject,
                existing.Predicate,
                existing.Object)],
            delete: [new DeleteFactOperation("f:sha256:" + new string('0', 64))]));
        False(result.Changed, "no-op marked changed");
        Equal(0L, result.AfterRevision, "no-op changed revision");
        Equal(0, result.AddedFactIds.Count, "no-op added facts");
        Equal(0, result.DeletedFactIds.Count, "no-op deleted facts");
        True(new FileInfo(store.LogPath).Length > 0, "no-op receipt was not durable");
    }

    using var reopened = Open(directory.Path, snapshot);
    Equal(0L, reopened.Revision, "no-op replay changed revision");
    True(reopened.TryGetReceipt("cmd-no-op", out var receipt), "no-op receipt missing");
    ResultsEqual(result, receipt!, "no-op replay receipt");
}

static void NormalizedRetryContent()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var first = CanonicalFact.Create(Person, EmailPredicate, LiteralObject.Plain("one"));
    var second = CanonicalFact.Create(Person, "urn:logiclens:test:note", LiteralObject.Plain("two"));
    using var store = Open(directory.Path, snapshot);
    var original = new ApplyDeltaCommand(
        "cmd-normalized",
        0,
        "user:sergey",
        add:
        [
            new AddFactOperation(second.Subject, second.Predicate, second.Object),
            new AddFactOperation(first.Subject, first.Predicate, first.Object),
            new AddFactOperation(second.Subject, second.Predicate, second.Object),
        ],
        delete:
        [
            new DeleteFactOperation("f:sha256:" + new string('1', 64)),
            new DeleteFactOperation("f:sha256:" + new string('1', 64)),
        ]);
    var accepted = store.ApplyDelta(original);
    var reordered = new ApplyDeltaCommand(
        "cmd-normalized",
        0,
        "user:sergey",
        add:
        [
            new AddFactOperation(first.Subject, first.Predicate, first.Object),
            new AddFactOperation(second.Subject, second.Predicate, second.Object),
        ],
        delete: [new DeleteFactOperation("f:sha256:" + new string('1', 64))]);
    ResultsEqual(accepted, store.ApplyDelta(reordered), "normalized retry");
}

static void IncompleteTailRecovery()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var injector = new ThrowOnceFaultInjector(RuntimeStateFaultPoint.AfterPayload);
    var options = Options(injector);
    var command = NewFactCommand("cmd-partial", 0, "partial");
    using (var store = RuntimeStateStore.Open(directory.Path, snapshot, options))
    {
        Throws<SimulatedCrashException>(
            () => store.ApplyDelta(command),
            "partial frame fault not raised");
        Throws<RuntimeStateFaultedException>(
            () => _ = store.Revision,
            "faulted store remained usable");
    }
    var logPath = System.IO.Path.Combine(directory.Path, RuntimeStateStore.LogFileName);
    True(new FileInfo(logPath).Length > 0, "partial frame was not written");

    using var reopened = Open(directory.Path, snapshot);
    Equal(0L, reopened.Revision, "partial frame changed revision");
    False(reopened.TryGetReceipt("cmd-partial", out _), "partial receipt survived");
    Equal(0L, new FileInfo(logPath).Length, "partial tail was not truncated");
}

static void DurableFrameRecovery()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var injector = new ThrowOnceFaultInjector(RuntimeStateFaultPoint.AfterDurableFlush);
    var command = NewFactCommand("cmd-durable", 0, "durable");
    using (var store = RuntimeStateStore.Open(directory.Path, snapshot, Options(injector)))
    {
        Throws<SimulatedCrashException>(
            () => store.ApplyDelta(command),
            "durable crash fault not raised");
    }

    using var reopened = Open(directory.Path, snapshot);
    Equal(1L, reopened.Revision, "durable frame was not replayed");
    True(reopened.TryGetReceipt("cmd-durable", out var receipt), "durable receipt missing");
    True(receipt!.Changed, "durable receipt marked no-op");
    ResultsEqual(receipt, reopened.ApplyDelta(command), "durable retry");
}

static void CommittedCorruptionRejection()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    string logPath;
    using (var store = Open(directory.Path, snapshot))
    {
        store.ApplyDelta(NewFactCommand("cmd-corrupt", 0, "corrupt"));
        logPath = store.LogPath;
    }
    var bytes = File.ReadAllBytes(logPath);
    True(bytes.Length > 18, "runtime frame is unexpectedly short");
    bytes[17] ^= 0x01;
    File.WriteAllBytes(logPath, bytes);
    Throws<RuntimeStateCorruptionException>(
        () => RuntimeStateStore.Open(directory.Path, snapshot).Dispose(),
        "committed corruption was accepted");
}

static void SnapshotIdentityPin()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    using (var store = Open(directory.Path, snapshot))
    {
        store.ApplyDelta(NewFactCommand("cmd-snapshot", 0, "snapshot"));
    }
    var other = new RuntimeStateSnapshot(
        "snapshot:other",
        snapshot.BaseRevision,
        snapshot.Facts);
    Throws<RuntimeStateCorruptionException>(
        () => RuntimeStateStore.Open(directory.Path, other).Dispose(),
        "wrong snapshot accepted journal");
}

static void ExclusiveWriter()
{
    using var directory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    using var first = Open(directory.Path, snapshot);
    Throws<RuntimeStateInUseException>(
        () => RuntimeStateStore.Open(directory.Path, snapshot).Dispose(),
        "second writer opened same state");
}

static void DeterministicJournalBytes()
{
    using var firstDirectory = new TemporaryDirectory();
    using var secondDirectory = new TemporaryDirectory();
    var snapshot = CreateSnapshot();
    var command = NewFactCommand("cmd-deterministic", 0, "same");
    string firstPath;
    string secondPath;
    using (var first = Open(firstDirectory.Path, snapshot))
    {
        first.ApplyDelta(command);
        firstPath = first.LogPath;
    }
    using (var second = Open(secondDirectory.Path, snapshot))
    {
        second.ApplyDelta(command);
        secondPath = second.LogPath;
    }
    True(
        File.ReadAllBytes(firstPath).AsSpan().SequenceEqual(File.ReadAllBytes(secondPath)),
        "same command produced different journal bytes");
}

static RuntimeStateStore Open(string path, RuntimeStateSnapshot snapshot) =>
    RuntimeStateStore.Open(path, snapshot, Options());

static RuntimeStateStoreOptions Options(IRuntimeStateFaultInjector? injector = null) =>
    new()
    {
        TimeProvider = new FixedTimeProvider(FixedNow),
        FaultInjector = injector,
    };

static RuntimeStateSnapshot CreateSnapshot()
{
    var fact = CanonicalFact.Create(
        Person,
        NamePredicate,
        LiteralObject.LanguageTagged("Alexey Vetrov", "en"));
    var origin = new ArchiveRuntimeFactOrigin(
        "origin:archive:1",
        "fixtures/zero-epoch/archive/person.fog",
        "archive",
        Person);
    return new RuntimeStateSnapshot(
        "snapshot:zero-epoch:test",
        0,
        [new RuntimeFactEntry(fact, [origin])]);
}

static ApplyDeltaCommand NewFactCommand(
    string commandId,
    long expectedRevision,
    string lexical) =>
    new(
        commandId,
        expectedRevision,
        "user:sergey",
        add:
        [
            new AddFactOperation(
                Person,
                "urn:logiclens:test:value",
                LiteralObject.Plain(lexical)),
        ]);

static void ResultsEqual(
    ApplyDeltaResult expected,
    ApplyDeltaResult actual,
    string context)
{
    Equal(expected.CommandId, actual.CommandId, context + " CommandId");
    Equal(expected.RequestHash, actual.RequestHash, context + " hash");
    Equal(expected.BeforeRevision, actual.BeforeRevision, context + " before");
    Equal(expected.AfterRevision, actual.AfterRevision, context + " after");
    Equal(expected.Changed, actual.Changed, context + " changed");
    Equal(expected.AcceptedAtUtc, actual.AcceptedAtUtc, context + " timestamp");
    SequenceEqual(expected.AddedFactIds, actual.AddedFactIds, context + " added");
    SequenceEqual(expected.DeletedFactIds, actual.DeletedFactIds, context + " deleted");
}

static T Single<T>(IEnumerable<T> values) => values.Single();

static void SequenceEqual<T>(
    IEnumerable<T> expected,
    IEnumerable<T> actual,
    string context)
{
    if (!expected.SequenceEqual(actual))
    {
        throw new InvalidOperationException($"{context}: sequences differ.");
    }
}

static void Equal<T>(T expected, T actual, string context)
{
    if (!EqualityComparer<T>.Default.Equals(expected, actual))
    {
        throw new InvalidOperationException(
            $"{context}: expected '{expected}', actual '{actual}'.");
    }
}

static void True(bool condition, string message)
{
    if (!condition)
    {
        throw new InvalidOperationException(message);
    }
}

static void False(bool condition, string message) => True(!condition, message);

static void Throws<TException>(Action action, string message)
    where TException : Exception
{
    try
    {
        action();
    }
    catch (TException)
    {
        return;
    }
    throw new InvalidOperationException(message);
}

const string Person = "urn:logiclens:person:alex";
const string NamePredicate = "http://fogid.net/o/name";
const string EmailPredicate = "urn:logiclens:test:email";
static readonly DateTimeOffset FixedNow =
    new(2026, 7, 25, 12, 0, 0, TimeSpan.Zero);

sealed class FixedTimeProvider(DateTimeOffset value) : TimeProvider
{
    public override DateTimeOffset GetUtcNow() => value;
}

sealed class SimulatedCrashException : Exception;

sealed class ThrowOnceFaultInjector(RuntimeStateFaultPoint target)
    : IRuntimeStateFaultInjector
{
    private bool thrown;

    public void OnFaultPoint(RuntimeStateFaultPoint point)
    {
        if (!thrown && point == target)
        {
            thrown = true;
            throw new SimulatedCrashException();
        }
    }
}

sealed class TemporaryDirectory : IDisposable
{
    public TemporaryDirectory()
    {
        Path = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            "logiclens-state-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path);
    }

    public string Path { get; }

    public void Dispose()
    {
        if (Directory.Exists(Path))
        {
            Directory.Delete(Path, recursive: true);
        }
    }
}
