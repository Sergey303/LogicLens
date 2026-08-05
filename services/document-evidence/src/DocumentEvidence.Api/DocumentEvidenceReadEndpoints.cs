using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

internal static class DocumentEvidenceReadEndpoints
{
    public static async Task<IResult> GetDocumentAsync(
        Guid workspaceId,
        Guid documentId,
        HttpRequest request,
        IDocumentEvidenceApiOperations operations,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await operations.GetDocumentAsync(
                DocumentEvidenceRequestHeaders.ActorId(request),
                workspaceId,
                documentId,
                cancellationToken
            );
            return result is null ? Results.NotFound() : Results.Ok(result);
        }
        catch (DocumentEvidenceApiException exception)
        {
            return DocumentEvidenceApiResults.Failure(exception);
        }
    }

    public static async Task<IResult> ListFragmentsAsync(
        Guid workspaceId,
        Guid revisionId,
        HttpRequest request,
        IDocumentEvidenceApiOperations operations,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await operations.ListFragmentsAsync(
                DocumentEvidenceRequestHeaders.ActorId(request),
                workspaceId,
                revisionId,
                cancellationToken
            );
            return Results.Ok(result);
        }
        catch (DocumentEvidenceApiException exception)
        {
            return DocumentEvidenceApiResults.Failure(exception);
        }
    }
}
