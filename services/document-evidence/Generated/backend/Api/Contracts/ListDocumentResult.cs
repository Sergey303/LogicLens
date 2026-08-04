#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListDocumentResult
{
    public IReadOnlyList<DocumentDto> Items { get; set; } = Array.Empty<DocumentDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
