using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

internal static class DocumentEvidenceReadPlanEndpoints
{
    public static async Task<IResult> IssueAsync(
        Guid workspaceId,
        Guid revisionId,
        HttpRequest request,
        IDocumentEvidenceReadPlanApiOperations operations,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await operations.IssueReadPlanAsync(
                DocumentEvidenceRequestHeaders.ActorId(request),
                workspaceId,
                revisionId,
                cancellationToken
            );
            return Results.Created(DocumentEvidenceApiV1.ReadPlan(workspaceId, revisionId), result);
        }
        catch (DocumentEvidenceApiException exception)
        {
            return DocumentEvidenceApiResults.Failure(exception);
        }
    }

    public static async Task<IResult> OpenAsync(
        HttpRequest request,
        HttpResponse response,
        IDocumentEvidenceReadPlanApiOperations operations,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var result = await operations.OpenReadPlanAsync(
                DocumentEvidenceRequestHeaders.ActorId(request),
                DocumentEvidenceRequestHeaders.ReadPlanToken(request),
                cancellationToken
            );
            response.ContentLength = result.SizeBytes;
            response.Headers[DocumentEvidenceApiV1.ContentSha256Header] = result.ContentSha256;
            return Results.Stream(result.Content, result.MediaType);
        }
        catch (DocumentEvidenceApiException exception)
        {
            return DocumentEvidenceApiResults.Failure(exception);
        }
    }
}
