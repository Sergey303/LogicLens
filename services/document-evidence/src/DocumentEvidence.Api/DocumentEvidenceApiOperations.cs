using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

public sealed record UploadRevisionRequest(
    Guid ActorId,
    Guid WorkspaceId,
    Guid DocumentId,
    string DisplayName,
    string IdempotencyKey,
    string MediaType,
    string SourceKind,
    long? DeclaredLength,
    Stream Content
);

public interface IDocumentEvidenceApiOperations
{
    Task<UploadRevisionDto> UploadRevisionAsync(
        UploadRevisionRequest request,
        CancellationToken cancellationToken
    );

    Task<DocumentMetadataDto?> GetDocumentAsync(
        Guid actorId,
        Guid workspaceId,
        Guid documentId,
        CancellationToken cancellationToken
    );

    Task<IReadOnlyList<DocumentFragmentDto>> ListFragmentsAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    );
}

public sealed class DocumentEvidenceApiException : Exception
{
    public DocumentEvidenceApiException(
        int statusCode,
        string code,
        string message,
        bool retryable = false,
        Exception? innerException = null
    ) : base(message, innerException)
    {
        StatusCode = statusCode;
        Code = code;
        Retryable = retryable;
    }

    public int StatusCode { get; }
    public string Code { get; }
    public bool Retryable { get; }
}
