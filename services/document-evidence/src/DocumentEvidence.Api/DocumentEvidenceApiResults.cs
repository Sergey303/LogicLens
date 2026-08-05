using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

internal static class DocumentEvidenceApiResults
{
    public static IResult Failure(DocumentEvidenceApiException exception)
    {
        return Results.Json(
            new DocumentEvidenceErrorDto(
                exception.Code,
                exception.Message,
                exception.Retryable
            ),
            statusCode: exception.StatusCode
        );
    }

    public static IResult Unexpected()
    {
        return Results.Json(
            new DocumentEvidenceErrorDto(
                "internal-error",
                "Document Evidence Service could not complete the request.",
                true
            ),
            statusCode: StatusCodes.Status500InternalServerError
        );
    }
}
