#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListDocumentRequest
{
    public int Page { get; set; } = 1;

    public int PageSize { get; set; } = 10;

    public List<ListDocumentFilter> Filters { get; set; } = new();

    public List<ListDocumentSort> Sort { get; set; } = new();
}

public sealed class ListDocumentFilter
{
    public string Field { get; set; } = string.Empty;

    public string Operator { get; set; } = "contains";

    public string? Value { get; set; }

    public List<string> Values { get; set; } = new();
}

public sealed class ListDocumentSort
{
    public string Field { get; set; } = string.Empty;

    public string Direction { get; set; } = "asc";
}
