#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListDocumentRevisionRequest
{
    public int Page { get; set; } = 1;

    public int PageSize { get; set; } = 10;

    public List<ListDocumentRevisionFilter> Filters { get; set; } = new();

    public List<ListDocumentRevisionSort> Sort { get; set; } = new();
}

public sealed class ListDocumentRevisionFilter
{
    public string Field { get; set; } = string.Empty;

    public string Operator { get; set; } = "contains";

    public string? Value { get; set; }

    public List<string> Values { get; set; } = new();
}

public sealed class ListDocumentRevisionSort
{
    public string Field { get; set; } = string.Empty;

    public string Direction { get; set; } = "asc";
}
