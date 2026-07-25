using LogicLens.Core.Graph;
using LogicLens.Core.Model;

namespace LogicLens.State;

public abstract record RuntimeFactOrigin
{
    protected RuntimeFactOrigin(string originId)
    {
        OriginId = StateGuard.Required(originId, nameof(originId));
    }

    public string OriginId { get; }
}

public sealed record ArchiveRuntimeFactOrigin : RuntimeFactOrigin
{
    public ArchiveRuntimeFactOrigin(
        string originId,
        string sourcePath,
        string sourceDbId,
        string entityId)
        : base(originId)
    {
        SourcePath = StateGuard.Required(sourcePath, nameof(sourcePath));
        SourceDbId = StateGuard.Required(sourceDbId, nameof(sourceDbId));
        EntityId = StateGuard.Required(entityId, nameof(entityId));
    }

    public string SourcePath { get; }

    public string SourceDbId { get; }

    public string EntityId { get; }
}

public sealed record EditRuntimeFactOrigin : RuntimeFactOrigin
{
    public EditRuntimeFactOrigin(
        string originId,
        string actor,
        string commandId,
        DateTimeOffset timestampUtc)
        : base(originId)
    {
        Actor = StateGuard.Required(actor, nameof(actor));
        CommandId = StateGuard.Required(commandId, nameof(commandId));
        TimestampUtc = timestampUtc.ToUniversalTime();
    }

    public string Actor { get; }

    public string CommandId { get; }

    public DateTimeOffset TimestampUtc { get; }
}

public sealed record RuntimeFactEntry
{
    public RuntimeFactEntry(
        CanonicalFact fact,
        IReadOnlyList<RuntimeFactOrigin> origins)
    {
        Fact = fact ?? throw new ArgumentNullException(nameof(fact));
        ArgumentNullException.ThrowIfNull(origins);
        Origins = origins
            .OrderBy(static origin => origin.OriginId, StringComparer.Ordinal)
            .ToArray();
        if (Origins.Count == 0)
        {
            throw new ArgumentException(
                "Every runtime fact must have at least one origin.",
                nameof(origins));
        }
        if (Origins.Select(static origin => origin.OriginId)
            .Distinct(StringComparer.Ordinal)
            .Count() != Origins.Count)
        {
            throw new ArgumentException(
                "Runtime fact origin identifiers must be unique.",
                nameof(origins));
        }
    }

    public CanonicalFact Fact { get; }

    public IReadOnlyList<RuntimeFactOrigin> Origins { get; }
}

public sealed class RuntimeStateSnapshot
{
    public RuntimeStateSnapshot(
        string snapshotId,
        long baseRevision,
        IReadOnlyList<RuntimeFactEntry> facts)
    {
        SnapshotId = StateGuard.Required(snapshotId, nameof(snapshotId));
        if (baseRevision < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(baseRevision),
                baseRevision,
                "Base revision cannot be negative.");
        }
        ArgumentNullException.ThrowIfNull(facts);
        BaseRevision = baseRevision;
        Facts = facts
            .OrderBy(static entry => entry.Fact.FactId, StringComparer.Ordinal)
            .ToArray();
        if (Facts.Select(static entry => entry.Fact.FactId)
            .Distinct(StringComparer.Ordinal)
            .Count() != Facts.Count)
        {
            throw new ArgumentException(
                "Snapshot FactIds must be unique.",
                nameof(facts));
        }
        foreach (var entry in Facts)
        {
            foreach (var archive in entry.Origins.OfType<ArchiveRuntimeFactOrigin>())
            {
                if (!StringComparer.Ordinal.Equals(
                        archive.EntityId,
                        entry.Fact.Subject))
                {
                    throw new ArgumentException(
                        $"Archive origin '{archive.OriginId}' belongs to " +
                        $"'{archive.EntityId}', not '{entry.Fact.Subject}'.",
                        nameof(facts));
                }
            }
        }
    }

    public string SnapshotId { get; }

    public long BaseRevision { get; }

    public IReadOnlyList<RuntimeFactEntry> Facts { get; }

    public static RuntimeStateSnapshot FromCanonicalGraph(
        string snapshotId,
        long baseRevision,
        CanonicalGraph graph)
    {
        ArgumentNullException.ThrowIfNull(graph);
        var facts = graph.Entries
            .Select(static entry => new RuntimeFactEntry(
                entry.Fact,
                entry.Origins
                    .Select(static origin => (RuntimeFactOrigin)
                        new ArchiveRuntimeFactOrigin(
                            origin.OriginId,
                            origin.SourcePath,
                            origin.SourceDbId,
                            origin.EntityId))
                    .ToArray()))
            .ToArray();
        return new RuntimeStateSnapshot(snapshotId, baseRevision, facts);
    }
}

public sealed record AddFactOperation
{
    public AddFactOperation(
        string subject,
        string predicate,
        FactObject @object)
    {
        Subject = StateGuard.Required(subject, nameof(subject));
        Predicate = StateGuard.Required(predicate, nameof(predicate));
        Object = @object ?? throw new ArgumentNullException(nameof(@object));
    }

    public string Subject { get; }

    public string Predicate { get; }

    public FactObject Object { get; }

    public CanonicalFact ToCanonicalFact() =>
        CanonicalFact.Create(Subject, Predicate, Object);
}

public sealed record DeleteFactOperation
{
    public DeleteFactOperation(string factId)
    {
        FactId = StateGuard.Required(factId, nameof(factId));
    }

    public string FactId { get; }
}

public sealed class ApplyDeltaCommand
{
    public ApplyDeltaCommand(
        string commandId,
        long expectedRevision,
        string actor,
        IReadOnlyList<AddFactOperation>? add = null,
        IReadOnlyList<DeleteFactOperation>? delete = null)
    {
        CommandId = StateGuard.Required(commandId, nameof(commandId));
        if (expectedRevision < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(expectedRevision),
                expectedRevision,
                "Expected revision cannot be negative.");
        }
        ExpectedRevision = expectedRevision;
        Actor = StateGuard.Required(actor, nameof(actor));
        Add = add?.ToArray() ?? [];
        Delete = delete?.ToArray() ?? [];
        if (Add.Any(static operation => operation is null))
        {
            throw new ArgumentException(
                "Add operations cannot contain null.",
                nameof(add));
        }
        if (Delete.Any(static operation => operation is null))
        {
            throw new ArgumentException(
                "Delete operations cannot contain null.",
                nameof(delete));
        }
    }

    public string CommandId { get; }

    public long ExpectedRevision { get; }

    public string Actor { get; }

    public IReadOnlyList<AddFactOperation> Add { get; }

    public IReadOnlyList<DeleteFactOperation> Delete { get; }
}

public sealed record ApplyDeltaResult(
    string CommandId,
    string RequestHash,
    long BeforeRevision,
    long AfterRevision,
    bool Changed,
    IReadOnlyList<string> AddedFactIds,
    IReadOnlyList<string> DeletedFactIds,
    DateTimeOffset AcceptedAtUtc);

public sealed record RuntimeStateView(
    string SnapshotId,
    long Revision,
    IReadOnlyList<RuntimeFactEntry> Facts);

internal static class StateGuard
{
    public static string Required(string? value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException(
                "Value cannot be null, empty, or whitespace.",
                parameterName);
        }
        return value;
    }
}
