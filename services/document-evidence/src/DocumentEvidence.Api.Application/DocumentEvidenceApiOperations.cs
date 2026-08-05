using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Security;
using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Application;

public sealed class DocumentEvidenceApiOperations : IDocumentEvidenceApiOperations
{
    private readonly DocumentEvidenceFacade _facade;
    private readonly SecureDocumentUploadService _uploads;

    public DocumentEvidenceApiOperations(
        SecureDocumentUploadService uploads,
        DocumentEvidenceFacade facade
    )
    {
        _uploads = uploads;
        _facade = facade;
    }

    public async Task<UploadRevisionDto> UploadRevisionAsync(
        UploadRevisionRequest request,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var adapter = TrustedAdapterCatalog.Resolve(request.MediaType);
            var result = await _uploads.CompleteAsync(
                new SecureUploadCommand(
                    request.ActorId,
                    request.WorkspaceId,
                    request.DocumentId,
                    request.DisplayName,
                    request.IdempotencyKey,
                    request.MediaType,
                    request.SourceKind,
                    adapter.Name,
                    adapter.Version,
                    request.DeclaredLength,
                    request.Content
                ),
                cancellationToken
            );
            var completion = result.Completion;
            return new UploadRevisionDto(
                completion.WorkspaceId,
                completion.DocumentId,
                completion.RevisionId,
                completion.RevisionNumber,
                completion.ProcessingJobId,
                completion.ManifestSha256,
                result.DisplayName,
                "Pending",
                completion.Replayed
            );
        }
        catch (Exception exception) when (TryMap(exception, out var mapped))
        {
            throw mapped;
        }
    }

    public async Task<DocumentMetadataDto?> GetDocumentAsync(
        Guid actorId,
        Guid workspaceId,
        Guid documentId,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await _facade.GetDocumentAsync(
                new GetDocumentQuery(actorId, new DocumentKey(workspaceId, documentId)),
                cancellationToken
            );
            return result is null ? null : DocumentEvidenceApiMapper.Document(result);
        }
        catch (Exception exception) when (TryMap(exception, out var mapped))
        {
            throw mapped;
        }
    }

    public async Task<IReadOnlyList<DocumentFragmentDto>> ListFragmentsAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await _facade.ListFragmentsAsync(
                new ListFragmentsQuery(actorId, workspaceId, revisionId),
                cancellationToken
            );
            return result.Select(DocumentEvidenceApiMapper.Fragment).ToArray();
        }
        catch (Exception exception) when (TryMap(exception, out var mapped))
        {
            throw mapped;
        }
    }

    private static bool TryMap(Exception exception, out DocumentEvidenceApiException mapped)
    {
        mapped = exception switch
        {
            UnauthorizedAccessException => new DocumentEvidenceApiException(
                StatusCodes.Status403Forbidden,
                "access-denied",
                "The actor cannot access this document workspace."
            ),
            UploadQuotaExceededException quota => new DocumentEvidenceApiException(
                StatusCodes.Status429TooManyRequests,
                quota.QuotaCode,
                "The upload quota has been exceeded.",
                retryable: true,
                quota
            ),
            InvalidDataException => new DocumentEvidenceApiException(
                StatusCodes.Status400BadRequest,
                "invalid-document-content",
                exception.Message
            ),
            ArgumentException => new DocumentEvidenceApiException(
                StatusCodes.Status400BadRequest,
                "invalid-request",
                exception.Message
            ),
            _ => null!,
        };
        return mapped is not null;
    }
}
