using LogicLens.Core.Model;

namespace LogicLens.State;

public sealed class RuntimeStateStore : IDisposable
{
    public const string LogFileName = "runtime-state.llog";

    private readonly object sync = new();
    private readonly RuntimeStateStoreOptions options;
    private readonly SortedDictionary<string, RuntimeFactEntry> facts;
    private readonly Dictionary<string, ReceiptEntry> receipts =
        new(StringComparer.Ordinal);
    private FileStream? stream;
    private long revision;
    private bool faulted;
    private bool disposed;

    private RuntimeStateStore(
        string directoryPath,
        RuntimeStateSnapshot snapshot,
        RuntimeStateStoreOptions options,
        FileStream stream)
    {
        DirectoryPath = directoryPath;
        SnapshotId = snapshot.SnapshotId;
        this.options = options;
        this.stream = stream;
        facts = new SortedDictionary<string, RuntimeFactEntry>(
            snapshot.Facts.ToDictionary(
                static entry => entry.Fact.FactId,
                static entry => entry,
                StringComparer.Ordinal),
            StringComparer.Ordinal);
        revision = snapshot.BaseRevision;
    }

    public string DirectoryPath { get; }

    public string LogPath => Path.Combine(DirectoryPath, LogFileName);

    public string SnapshotId { get; }

    public long Revision
    {
        get
        {
            lock (sync)
            {
                EnsureUsable();
                return revision;
            }
        }
    }

    public static RuntimeStateStore Open(
        string directoryPath,
        RuntimeStateSnapshot snapshot,
        RuntimeStateStoreOptions? options = null)
    {
        if (string.IsNullOrWhiteSpace(directoryPath))
        {
            throw new ArgumentException(
                "Runtime state directory cannot be null, empty, or whitespace.",
                nameof(directoryPath));
        }
        ArgumentNullException.ThrowIfNull(snapshot);
        options ??= new RuntimeStateStoreOptions();
        options.Validate();

        var absoluteDirectory = Path.GetFullPath(directoryPath);
        Directory.CreateDirectory(absoluteDirectory);
        var logPath = Path.Combine(absoluteDirectory, LogFileName);
        FileStream stream;
        try
        {
            stream = new FileStream(
                logPath,
                FileMode.OpenOrCreate,
                FileAccess.ReadWrite,
                FileShare.Read,
                bufferSize: 4096,
                FileOptions.WriteThrough);
        }
        catch (IOException exception)
        {
            throw new RuntimeStateInUseException(logPath, exception);
        }

        var store = new RuntimeStateStore(
            absoluteDirectory,
            snapshot,
            options,
            stream);
        try
        {
            var records = RuntimeStateLogCodec.ReadAndRepairTail(stream, options);
            store.Replay(records);
            return store;
        }
        catch
        {
            stream.Dispose();
            throw;
        }
    }

    public ApplyDeltaResult ApplyDelta(ApplyDeltaCommand command)
    {
        var normalized = DeltaNormalizer.Normalize(command, options);
        lock (sync)
        {
            EnsureUsable();
            if (receipts.TryGetValue(command.CommandId, out var previous))
            {
                if (!StringComparer.Ordinal.Equals(
                        previous.RequestHash,
                        normalized.RequestHash))
                {
                    throw new RuntimeCommandConflictException(command.CommandId);
                }
                return previous.Result;
            }
            if (command.ExpectedRevision != revision)
            {
                throw new RuntimeRevisionConflictException(
                    command.ExpectedRevision,
                    revision);
            }

            var addById = normalized.Add.ToDictionary(
                static fact => fact.FactId,
                static fact => fact,
                StringComparer.Ordinal);
            var deleteSet = normalized.Delete.ToHashSet(StringComparer.Ordinal);
            var actualDelete = normalized.Delete
                .Where(factId => facts.ContainsKey(factId)
                    && !addById.ContainsKey(factId))
                .ToArray();
            var actualAdd = normalized.Add
                .Where(fact => !facts.ContainsKey(fact.FactId))
                .ToArray();

            foreach (var fact in normalized.Add)
            {
                if (facts.TryGetValue(fact.FactId, out var existing)
                    && !SameFact(existing.Fact, fact))
                {
                    throw new InvalidOperationException(
                        $"FactId collision detected for '{fact.FactId}'.");
                }
            }
            foreach (var factId in actualDelete)
            {
                if (!deleteSet.Contains(factId))
                {
                    throw new InvalidOperationException(
                        "Internal delta normalization error.");
                }
            }

            var acceptedAtUtc = options.TimeProvider.GetUtcNow().ToUniversalTime();
            var record = RuntimeLogRecord.Create(
                SnapshotId,
                command,
                normalized.RequestHash,
                revision,
                acceptedAtUtc,
                actualAdd,
                actualDelete);

            try
            {
                RuntimeStateLogCodec.Append(
                    stream
                    ?? throw new ObjectDisposedException(nameof(RuntimeStateStore)),
                    record,
                    options);
            }
            catch
            {
                faulted = true;
                stream?.Dispose();
                stream = null;
                throw;
            }

            ApplyRecordToMemory(record, replay: false);
            var result = record.ToResult();
            receipts.Add(
                command.CommandId,
                new ReceiptEntry(normalized.RequestHash, result));
            return result;
        }
    }

    public RuntimeStateView GetView()
    {
        lock (sync)
        {
            EnsureUsable();
            return new RuntimeStateView(
                SnapshotId,
                revision,
                facts.Values.ToArray());
        }
    }

    public bool TryGetFact(string factId, out RuntimeFactEntry? entry)
    {
        factId = StateGuard.Required(factId, nameof(factId));
        lock (sync)
        {
            EnsureUsable();
            return facts.TryGetValue(factId, out entry);
        }
    }

    public bool TryGetReceipt(string commandId, out ApplyDeltaResult? result)
    {
        commandId = StateGuard.Required(commandId, nameof(commandId));
        lock (sync)
        {
            EnsureUsable();
            if (receipts.TryGetValue(commandId, out var receipt))
            {
                result = receipt.Result;
                return true;
            }
            result = null;
            return false;
        }
    }

    public void Dispose()
    {
        lock (sync)
        {
            if (disposed)
            {
                return;
            }
            disposed = true;
            stream?.Dispose();
            stream = null;
        }
    }

    private void Replay(IReadOnlyList<RuntimeLogRecord> records)
    {
        foreach (var record in records)
        {
            if (!StringComparer.Ordinal.Equals(record.SnapshotId, SnapshotId))
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log belongs to snapshot '{record.SnapshotId}', " +
                    $"not '{SnapshotId}'.");
            }
            if (record.BeforeRevision != revision)
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log revision chain expected {revision}, but frame " +
                    $"starts at {record.BeforeRevision}.");
            }
            if (receipts.ContainsKey(record.CommandId))
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log contains duplicate CommandId '{record.CommandId}'.");
            }

            ApplyRecordToMemory(record, replay: true);
            var result = record.ToResult();
            receipts.Add(
                record.CommandId,
                new ReceiptEntry(record.RequestHash, result));
        }
    }

    private void ApplyRecordToMemory(RuntimeLogRecord record, bool replay)
    {
        foreach (var factId in record.Delete)
        {
            if (!facts.Remove(factId) && replay)
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log deletes absent fact '{factId}'.");
            }
        }
        foreach (var item in record.Add)
        {
            if (facts.ContainsKey(item.Fact.FactId))
            {
                if (replay)
                {
                    throw new RuntimeStateCorruptionException(
                        $"Runtime log adds existing fact '{item.Fact.FactId}'.");
                }
                throw new InvalidOperationException(
                    $"Fact '{item.Fact.FactId}' already exists.");
            }
            facts.Add(
                item.Fact.FactId,
                new RuntimeFactEntry(
                    item.Fact,
                    new RuntimeFactOrigin[] { item.Origin }));
        }
        revision = record.AfterRevision;
    }

    private void EnsureUsable()
    {
        ObjectDisposedException.ThrowIf(disposed, this);
        if (faulted)
        {
            throw new RuntimeStateFaultedException();
        }
    }

    private static bool SameFact(CanonicalFact left, CanonicalFact right) =>
        StringComparer.Ordinal.Equals(left.Subject, right.Subject)
        && StringComparer.Ordinal.Equals(left.Predicate, right.Predicate)
        && Equals(left.Object, right.Object);

    private sealed record ReceiptEntry(
        string RequestHash,
        ApplyDeltaResult Result);
}
