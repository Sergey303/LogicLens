#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListDocumentRevisionResult
{
    public IReadOnlyList<DocumentRevisionDto> Items { get; set; } = Array.Empty<DocumentRevisionDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
