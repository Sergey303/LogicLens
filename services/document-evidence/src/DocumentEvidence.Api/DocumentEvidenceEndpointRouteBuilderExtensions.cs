using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

public static class DocumentEvidenceEndpointRouteBuilderExtensions
{
    public static IEndpointRouteBuilder MapDocumentEvidenceV1(
        this IEndpointRouteBuilder endpoints
    )
    {
        var group = endpoints.MapGroup("/api/v1/workspaces/{workspaceId:guid}");
        group.MapPut(
            "/documents/{documentId:guid}/revisions",
            DocumentEvidenceUploadEndpoint.HandleAsync
        );
        group.MapGet(
            "/documents/{documentId:guid}",
            DocumentEvidenceReadEndpoints.GetDocumentAsync
        );
        group.MapGet(
            "/revisions/{revisionId:guid}/fragments",
            DocumentEvidenceReadEndpoints.ListFragmentsAsync
        );
        return endpoints;
    }
}
