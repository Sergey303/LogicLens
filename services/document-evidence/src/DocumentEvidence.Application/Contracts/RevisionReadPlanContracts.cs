namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public sealed record IssueRevisionReadPlanCommand(
    Guid ActorId,
    Guid WorkspaceId,
    Guid RevisionId
);

public sealed record ExecuteRevisionReadPlanCommand(
    Guid ActorId,
    string Token
);

public sealed record RevisionReadPlan(
    string Token,
    Guid PlanId,
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    string ObjectSha256,
    long SizeBytes,
    string MediaType,
    DateTimeOffset ExpiresAtUtc
);

public sealed record RevisionReadPlanPayload(
    int Version,
    Guid PlanId,
    Guid ActorId,
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    string ObjectSha256,
    long SizeBytes,
    string MediaType,
    DateTimeOffset IssuedAtUtc,
    DateTimeOffset ExpiresAtUtc
);
