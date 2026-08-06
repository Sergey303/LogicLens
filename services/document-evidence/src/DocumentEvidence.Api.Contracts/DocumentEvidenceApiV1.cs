namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

public static class DocumentEvidenceApiV1
{
    public const string ActorHeader = "X-Actor-Id";
    public const string FileNameHeader = "X-File-Name";
    public const string IdempotencyHeader = "Idempotency-Key";
    public const string SourceKindHeader = "X-Source-Kind";
    public const string ReadPlanTokenHeader = "X-Read-Plan-Token";
    public const string ContentSha256Header = "X-Content-Sha256";
    public const string Prefix = "/api/v1";

    public static string UploadRevision(Guid workspaceId, Guid documentId) =>
        $"{Prefix}/workspaces/{workspaceId:D}/documents/{documentId:D}/revisions";

    public static string Document(Guid workspaceId, Guid documentId) =>
        $"{Prefix}/workspaces/{workspaceId:D}/documents/{documentId:D}";

    public static string Fragments(Guid workspaceId, Guid revisionId) =>
        $"{Prefix}/workspaces/{workspaceId:D}/revisions/{revisionId:D}/fragments";

    public static string Processing(Guid workspaceId, Guid jobId) =>
        $"{Prefix}/workspaces/{workspaceId:D}/processing-jobs/{jobId:D}";

    public static string ReadPlan(Guid workspaceId, Guid revisionId) =>
        $"{Prefix}/workspaces/{workspaceId:D}/revisions/{revisionId:D}/read-plans";

    public static string ReadPlanContent() => $"{Prefix}/read-plans/content";
}
