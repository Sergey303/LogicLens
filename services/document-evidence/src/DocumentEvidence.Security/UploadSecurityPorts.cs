namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public interface IUploadAuthorizationPolicy
{
    ValueTask DemandWorkspaceUploadAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    );
}

public interface IUploadQuotaGate
{
    ValueTask DemandRequestAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    );

    ValueTask DemandBytesAsync(
        Guid workspaceId,
        long sizeBytes,
        CancellationToken cancellationToken
    );
}

public interface IUploadAuditSink
{
    ValueTask RecordAsync(
        UploadAuditRecord record,
        CancellationToken cancellationToken
    );
}
