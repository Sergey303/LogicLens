using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public sealed record SecureUploadOptions(
    long MaxUploadBytes = 67_108_864,
    int MaxDisplayNameLength = 180
);

public sealed record SecureUploadCommand(
    Guid ActorId,
    Guid WorkspaceId,
    Guid DocumentId,
    string DisplayName,
    string IdempotencyKey,
    string MediaType,
    string SourceKind,
    string Adapter,
    string AdapterVersion,
    long? DeclaredLength,
    Stream Content
);

public sealed record SecureUploadResult(
    string DisplayName,
    UploadCompletionResult Completion
);

public sealed record UploadAuditRecord(
    string EventType,
    Guid ActorId,
    Guid WorkspaceId,
    Guid DocumentId,
    string MediaType,
    long SizeBytes,
    string Outcome,
    DateTimeOffset OccurredAtUtc
);

public sealed class UploadQuotaExceededException : InvalidOperationException
{
    public UploadQuotaExceededException(string quotaCode)
        : base($"Upload quota exceeded: {quotaCode}")
    {
        QuotaCode = quotaCode;
    }

    public string QuotaCode { get; }
}
