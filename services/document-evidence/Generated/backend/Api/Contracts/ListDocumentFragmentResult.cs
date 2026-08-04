#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListDocumentFragmentResult
{
    public IReadOnlyList<DocumentFragmentDto> Items { get; set; } = Array.Empty<DocumentFragmentDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
