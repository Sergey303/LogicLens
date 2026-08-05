namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public sealed record CompleteUploadCommand(
    Guid WorkspaceId,
    Guid DocumentId,
    string IdempotencyKey,
    string MediaType,
    string SourceKind,
    string Adapter,
    string AdapterVersion,
    Stream Content
);

public sealed record RevisionManifest(
    int FormatVersion,
    string ObjectSha256,
    long SizeBytes,
    string MediaType,
    string SourceKind,
    string Adapter,
    string AdapterVersion,
    string CanonicalJson,
    string Sha256
);

public sealed record UploadCompletionCommit(
    Guid WorkspaceId,
    Guid DocumentId,
    string IdempotencyKey,
    StoredObjectReference StoredObject,
    RevisionManifest Manifest
);

public sealed record UploadCompletionResult(
    Guid WorkspaceId,
    Guid DocumentId,
    Guid RevisionId,
    int RevisionNumber,
    Guid StoredObjectId,
    Guid ProcessingJobId,
    string ManifestSha256,
    bool Replayed
);
