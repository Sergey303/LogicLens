using System.Text.Json;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

public sealed record DocumentEvidenceErrorDto(
    string Code,
    string Message,
    bool Retryable
);

public sealed record UploadRevisionDto(
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    Guid ProcessingJobId,
    string ManifestSha256,
    string DisplayName,
    string ProcessingState,
    bool Replayed
);

public sealed record DocumentMetadataDto(
    Guid WorkspaceId,
    Guid DocumentId,
    string DisplayName,
    string MediaType,
    string SourceKind,
    string State,
    int CurrentRevisionNumber,
    bool IsRevoked
);

public sealed record FragmentAnchorDto(
    string Kind,
    JsonElement Value
);

public sealed record DocumentFragmentDto(
    Guid FragmentId,
    Guid RevisionId,
    int Sequence,
    string Kind,
    FragmentAnchorDto Anchor,
    string Text,
    string ContentSha256
);

public sealed record ProcessingStateDto(
    Guid JobId,
    Guid RevisionId,
    string State,
    int Attempt,
    int MaxAttempts,
    DateTimeOffset AvailableAtUtc,
    string? LastErrorCode
);

public sealed record ReadPlanDto(
    Guid PlanId,
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    DateTimeOffset ExpiresAtUtc,
    string MediaType,
    long SizeBytes,
    string ContentSha256,
    string Token
);
