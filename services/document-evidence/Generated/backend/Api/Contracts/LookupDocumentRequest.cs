#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class LookupDocumentRequest
{
    public string? Query { get; set; }
    public int Take { get; set; } = 10;
}
