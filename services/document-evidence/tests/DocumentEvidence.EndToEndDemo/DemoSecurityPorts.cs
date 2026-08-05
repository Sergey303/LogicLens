using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoUploadAuthorizationPolicy : IUploadAuthorizationPolicy
{
    public ValueTask DemandWorkspaceUploadAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (actorId == Guid.Empty || workspaceId == Guid.Empty)
        {
            throw new UnauthorizedAccessException();
        }
        return ValueTask.CompletedTask;
    }
}

internal sealed class DemoUploadAuditSink : IUploadAuditSink
{
    private readonly List<UploadAuditRecord> _records = [];

    public IReadOnlyList<UploadAuditRecord> Records => _records;

    public ValueTask RecordAsync(
        UploadAuditRecord record,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        _records.Add(record);
        return ValueTask.CompletedTask;
    }
}
