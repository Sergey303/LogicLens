namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public sealed record ProtectedRevisionObject(
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    string Sha256,
    long SizeBytes,
    string MediaType,
    bool IsRevoked,
    bool IsSuperseded
);

public sealed record OpenRevisionBytesQuery(
    Guid ActorId,
    Guid WorkspaceId,
    Guid RevisionId
);
