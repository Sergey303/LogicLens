using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

internal static class DocumentEvidenceRequestHeaders
{
    public static Guid ActorId(HttpRequest request)
    {
        var value = DemandSingle(request, DocumentEvidenceApiV1.ActorHeader, 80);
        return Guid.TryParse(value, out var actorId) && actorId != Guid.Empty
            ? actorId
            : throw BadRequest("invalid-actor-id", "X-Actor-Id must be a non-empty GUID.");
    }

    public static string FileName(HttpRequest request)
    {
        return DemandSingle(request, DocumentEvidenceApiV1.FileNameHeader, 512);
    }

    public static string IdempotencyKey(HttpRequest request)
    {
        return DemandSingle(request, DocumentEvidenceApiV1.IdempotencyHeader, 160);
    }

    public static string SourceKind(HttpRequest request)
    {
        var value = request.Headers[DocumentEvidenceApiV1.SourceKindHeader].ToString().Trim();
        return value.Length == 0 ? "Upload" : DemandLength(value, 80, "invalid-source-kind");
    }

    private static string DemandSingle(HttpRequest request, string header, int maxLength)
    {
        var values = request.Headers[header];
        if (values.Count != 1)
        {
            throw BadRequest("missing-header", $"Exactly one {header} header is required.");
        }
        return DemandLength(values[0]?.Trim() ?? "", maxLength, "invalid-header");
    }

    private static string DemandLength(string value, int maxLength, string code)
    {
        if (value.Length is < 1 || value.Length > maxLength)
        {
            throw BadRequest(code, $"Header value must contain 1-{maxLength} characters.");
        }
        return value;
    }

    private static DocumentEvidenceApiException BadRequest(string code, string message) =>
        new(StatusCodes.Status400BadRequest, code, message);
}
