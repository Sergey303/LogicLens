using LogicLens.Core.Model;
using LogicLens.State;

internal static class MainProgram
{
    private const string Person = "urn:logiclens:person:alex";
    private const string Name = "http://fogid.net/o/name";
    private static readonly DateTimeOffset Now =
        new(2026, 7, 25, 12, 0, 0, TimeSpan.Zero);

    public static int Main()
    {
        Run("delta, replacement, replay, idempotency", DeltaReplacementReplay);
        Run("no-op and normalized retry", NoOpAndNormalizedRetry);
        Run("incomplete frame recovery", IncompleteFrameRecovery);
        Run("durable frame recovery", DurableFrameRecovery);
        Run("corruption and snapshot protection", CorruptionAndSnapshotProtection);
        Run("single writer and deterministic bytes", SingleWriterAndDeterminism);
        Console.WriteLine("LogicLens runtime state verification passed.");
        return 0;
    }

    private static void DeltaReplacementReplay()
    {
        using var temp = new TempDirectory();
        var snapshot = Snapshot();
        var email = Fact("urn:test:email", "alex@example.invalid");
        var add = AddCommand("cmd-add", 0, email);
        ApplyDeltaResult first;
        long durableLength;

        using (var store = Open(temp.Path, snapshot))
        {
            first = store.ApplyDelta(add);
            Check(first.Changed && first.AfterRevision == 1, "add revision");
            Check(store.TryGetFact(email.FactId, out var entry), "added fact missing");
            var origin = entry!.Origins.OfType<EditRuntimeFactOrigin>().Single();
            Equal("cmd-add", origin.CommandId, "origin command");
            Equal(Now, origin.TimestampUtc, "origin timestamp");
            SameResult(first, store.ApplyDelta(add), "exact retry");
            durableLength = new FileInfo(store.LogPath).Length;

            Throws<RuntimeCommandConflictException>(() => store.ApplyDelta(
                AddCommand("cmd-add", 0, Fact("urn:test:email", "different"))));
            Equal(durableLength, new FileInfo(store.LogPath).Length, "conflict wrote bytes");

            Throws<RuntimeRevisionConflictException>(() => store.ApplyDelta(
                new ApplyDeltaCommand(
                    "cmd-stale",
                    0,
                    "user:sergey",
                    delete: [new DeleteFactOperation(email.FactId)])));
            Check(!store.TryGetReceipt("cmd-stale", out _), "stale receipt persisted");
            Equal(durableLength, new FileInfo(store.LogPath).Length, "stale wrote bytes");

            var oldName = snapshot.Facts.Single().Fact;
            var newName = CanonicalFact.Create(
                Person,
                Name,
                LiteralObject.LanguageTagged("Алексей Ветров", "ru"));
            var replaced = store.ApplyDelta(new ApplyDeltaCommand(
                "cmd-replace",
                1,
                "user:sergey",
                add: [Add(newName)],
                delete: [new DeleteFactOperation(oldName.FactId)]));
            Check(replaced.AfterRevision == 2, "replacement revision");
            Sequence([newName.FactId], replaced.AddedFactIds, "replacement add");
            Sequence([oldName.FactId], replaced.DeletedFactIds, "replacement delete");
        }

        using var reopened = Open(temp.Path, snapshot);
        Equal(2L, reopened.Revision, "replayed revision");
        Check(reopened.TryGetReceipt("cmd-add", out var receipt), "receipt missing");
        SameResult(first, receipt!, "replayed receipt");
        SameResult(first, reopened.ApplyDelta(add), "retry after later revision");

        var original = snapshot.Facts.Single().Fact;
        var readd = reopened.ApplyDelta(AddCommand("cmd-readd", 2, original));
        Equal(original.FactId, readd.AddedFactIds.Single(), "FactId changed on re-add");
    }

    private static void NoOpAndNormalizedRetry()
    {
        using var temp = new TempDirectory();
        var snapshot = Snapshot();
        var existing = snapshot.Facts.Single().Fact;
        ApplyDeltaResult noOp;
        using (var store = Open(temp.Path, snapshot))
        {
            noOp = store.ApplyDelta(new ApplyDeltaCommand(
                "cmd-no-op",
                0,
                "user:sergey",
                add: [Add(existing)],
                delete: [new DeleteFactOperation(FakeId('0'))]));
            Check(!noOp.Changed && noOp.AfterRevision == 0, "no-op semantics");
        }
        using (var reopened = Open(temp.Path, snapshot))
        {
            Check(reopened.TryGetReceipt("cmd-no-op", out var receipt), "no-op receipt missing");
            SameResult(noOp, receipt!, "no-op replay");

            var one = Fact("urn:test:one", "one");
            var two = Fact("urn:test:two", "two");
            var accepted = reopened.ApplyDelta(new ApplyDeltaCommand(
                "cmd-normalized",
                0,
                "user:sergey",
                add: [Add(two), Add(one), Add(two)],
                delete:
                [
                    new DeleteFactOperation(FakeId('1')),
                    new DeleteFactOperation(FakeId('1')),
                ]));
            var retry = reopened.ApplyDelta(new ApplyDeltaCommand(
                "cmd-normalized",
                0,
                "user:sergey",
                add: [Add(one), Add(two)],
                delete: [new DeleteFactOperation(FakeId('1'))]));
            SameResult(accepted, retry, "normalized retry");
        }
    }

    private static void IncompleteFrameRecovery()
    {
        using var temp = new TempDirectory();
        var snapshot = Snapshot();
        using (var store = RuntimeStateStore.Open(
                   temp.Path,
                   snapshot,
                   Options(new ThrowAt(RuntimeStateFaultPoint.AfterPayload))))
        {
            Throws<SimulatedCrash>(() => store.ApplyDelta(
                AddCommand("cmd-partial", 0, Fact("urn:test:value", "partial"))));
            Throws<RuntimeStateFaultedException>(() => _ = store.Revision);
        }

        var log = Path.Combine(temp.Path, RuntimeStateStore.LogFileName);
        Check(new FileInfo(log).Length > 0, "partial bytes missing");
        using var reopened = Open(temp.Path, snapshot);
        Equal(0L, reopened.Revision, "partial frame changed revision");
        Check(!reopened.TryGetReceipt("cmd-partial", out _), "partial receipt survived");
        Equal(0L, new FileInfo(log).Length, "partial tail not truncated");
    }

    private static void DurableFrameRecovery()
    {
        using var temp = new TempDirectory();
        var snapshot = Snapshot();
        var command = AddCommand("cmd-durable", 0, Fact("urn:test:value", "durable"));
        using (var store = RuntimeStateStore.Open(
                   temp.Path,
                   snapshot,
                   Options(new ThrowAt(RuntimeStateFaultPoint.AfterDurableFlush))))
        {
            Throws<SimulatedCrash>(() => store.ApplyDelta(command));
        }

        using var reopened = Open(temp.Path, snapshot);
        Equal(1L, reopened.Revision, "durable frame not replayed");
        Check(reopened.TryGetReceipt("cmd-durable", out var receipt), "durable receipt missing");
        SameResult(receipt!, reopened.ApplyDelta(command), "durable retry");
    }

    private static void CorruptionAndSnapshotProtection()
    {
        using var corruptTemp = new TempDirectory();
        var snapshot = Snapshot();
        string log;
        using (var store = Open(corruptTemp.Path, snapshot))
        {
            store.ApplyDelta(AddCommand("cmd-corrupt", 0, Fact("urn:test:value", "bad")));
            log = store.LogPath;
        }
        var bytes = File.ReadAllBytes(log);
        bytes[17] ^= 0x01;
        File.WriteAllBytes(log, bytes);
        Throws<RuntimeStateCorruptionException>(() =>
            RuntimeStateStore.Open(corruptTemp.Path, snapshot).Dispose());

        using var snapshotTemp = new TempDirectory();
        using (var store = Open(snapshotTemp.Path, snapshot))
        {
            store.ApplyDelta(AddCommand("cmd-snapshot", 0, Fact("urn:test:value", "pin")));
        }
        var wrong = new RuntimeStateSnapshot("snapshot:other", 0, snapshot.Facts);
        Throws<RuntimeStateCorruptionException>(() =>
            RuntimeStateStore.Open(snapshotTemp.Path, wrong).Dispose());
    }

    private static void SingleWriterAndDeterminism()
    {
        var snapshot = Snapshot();
        using (var temp = new TempDirectory())
        using (var first = Open(temp.Path, snapshot))
        {
            Throws<RuntimeStateInUseException>(() =>
                RuntimeStateStore.Open(temp.Path, snapshot).Dispose());
        }

        using var left = new TempDirectory();
        using var right = new TempDirectory();
        var command = AddCommand("cmd-same", 0, Fact("urn:test:value", "same"));
        string leftLog;
        string rightLog;
        using (var store = Open(left.Path, snapshot))
        {
            store.ApplyDelta(command);
            leftLog = store.LogPath;
        }
        using (var store = Open(right.Path, snapshot))
        {
            store.ApplyDelta(command);
            rightLog = store.LogPath;
        }
        Check(
            File.ReadAllBytes(leftLog).AsSpan().SequenceEqual(File.ReadAllBytes(rightLog)),
            "journal bytes are not deterministic");
    }

    private static RuntimeStateSnapshot Snapshot()
    {
        var fact = CanonicalFact.Create(
            Person,
            Name,
            LiteralObject.LanguageTagged("Alexey Vetrov", "en"));
        return new RuntimeStateSnapshot(
            "snapshot:zero-epoch:test",
            0,
            [
                new RuntimeFactEntry(
                    fact,
                    [
                        new ArchiveRuntimeFactOrigin(
                            "origin:archive:1",
                            "fixtures/zero-epoch/archive/person.fog",
                            "archive",
                            Person),
                    ]),
            ]);
    }

    private static RuntimeStateStore Open(string path, RuntimeStateSnapshot snapshot) =>
        RuntimeStateStore.Open(path, snapshot, Options());

    private static RuntimeStateStoreOptions Options(IRuntimeStateFaultInjector? fault = null) =>
        new()
        {
            TimeProvider = new FixedTime(Now),
            FaultInjector = fault,
        };

    private static CanonicalFact Fact(string predicate, string lexical) =>
        CanonicalFact.Create(Person, predicate, LiteralObject.Plain(lexical));

    private static AddFactOperation Add(CanonicalFact fact) =>
        new(fact.Subject, fact.Predicate, fact.Object);

    private static ApplyDeltaCommand AddCommand(
        string commandId,
        long revision,
        CanonicalFact fact) =>
        new(commandId, revision, "user:sergey", add: [Add(fact)]);

    private static string FakeId(char value) => "f:sha256:" + new string(value, 64);

    private static void SameResult(
        ApplyDeltaResult expected,
        ApplyDeltaResult actual,
        string name)
    {
        Equal(expected.CommandId, actual.CommandId, name + " command");
        Equal(expected.RequestHash, actual.RequestHash, name + " hash");
        Equal(expected.BeforeRevision, actual.BeforeRevision, name + " before");
        Equal(expected.AfterRevision, actual.AfterRevision, name + " after");
        Equal(expected.Changed, actual.Changed, name + " changed");
        Equal(expected.AcceptedAtUtc, actual.AcceptedAtUtc, name + " timestamp");
        Sequence(expected.AddedFactIds, actual.AddedFactIds, name + " add");
        Sequence(expected.DeletedFactIds, actual.DeletedFactIds, name + " delete");
    }

    private static void Run(string name, Action test)
    {
        test();
        Console.WriteLine("PASS: " + name);
    }

    private static void Sequence<T>(IEnumerable<T> expected, IEnumerable<T> actual, string name)
    {
        Check(expected.SequenceEqual(actual), name);
    }

    private static void Equal<T>(T expected, T actual, string name)
    {
        Check(EqualityComparer<T>.Default.Equals(expected, actual),
            $"{name}: expected '{expected}', actual '{actual}'");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void Throws<T>(Action action) where T : Exception
    {
        try
        {
            action();
        }
        catch (T)
        {
            return;
        }
        throw new InvalidOperationException("Expected exception: " + typeof(T).Name);
    }

    private sealed class FixedTime(DateTimeOffset value) : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => value;
    }

    private sealed class SimulatedCrash : Exception
    {
    }

    private sealed class ThrowAt(RuntimeStateFaultPoint target) : IRuntimeStateFaultInjector
    {
        private bool thrown;

        public void OnFaultPoint(RuntimeStateFaultPoint point)
        {
            if (!thrown && point == target)
            {
                thrown = true;
                throw new SimulatedCrash();
            }
        }
    }

    private sealed class TempDirectory : IDisposable
    {
        public TempDirectory()
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
}
