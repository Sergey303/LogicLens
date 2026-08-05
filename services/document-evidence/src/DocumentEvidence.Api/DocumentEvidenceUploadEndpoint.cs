using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

internal static class DocumentEvidenceUploadEndpoint
{
    public static async Task<IResult> HandleAsync(
        Guid workspaceId,
        Guid documentId,
        HttpRequest request,
        IDocumentEvidenceApiOperations operations,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var mediaType = request.ContentType?.Split(';', 2)[0].Trim();
            if (string.IsNullOrWhiteSpace(mediaType))
            {
                throw new DocumentEvidenceApiException(
                    StatusCodes.Status415UnsupportedMediaType,
                    "missing-media-type",
                    "A supported Content-Type is required."
                );
            }
            var upload = new UploadRevisionRequest(
                DocumentEvidenceRequestHeaders.ActorId(request),
                workspaceId,
                documentId,
                DocumentEvidenceRequestHeaders.FileName(request),
                DocumentEvidenceRequestHeaders.IdempotencyKey(request),
                mediaType,
                DocumentEvidenceRequestHeaders.SourceKind(request),
                request.ContentLength,
                request.Body
            );
            var result = await operations.UploadRevisionAsync(upload, cancellationToken);
            return Results.Json(result, statusCode: StatusCodes.Status201Created);
        }
        catch (DocumentEvidenceApiException exception)
        {
            return DocumentEvidenceApiResults.Failure(exception);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception)
        {
            return DocumentEvidenceApiResults.Unexpected();
        }
    }
}
