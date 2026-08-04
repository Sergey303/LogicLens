#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListStaffPositionAssignmentRequest
{
    public int Page { get; set; } = 1;

    public int PageSize { get; set; } = 10;

    public List<ListStaffPositionAssignmentFilter> Filters { get; set; } = new();

    public List<ListStaffPositionAssignmentSort> Sort { get; set; } = new();
}

public sealed class ListStaffPositionAssignmentFilter
{
    public string Field { get; set; } = string.Empty;

    public string Operator { get; set; } = "contains";

    public string? Value { get; set; }

    public List<string> Values { get; set; } = new();
}

public sealed class ListStaffPositionAssignmentSort
{
    public string Field { get; set; } = string.Empty;

    public string Direction { get; set; } = "asc";
}
