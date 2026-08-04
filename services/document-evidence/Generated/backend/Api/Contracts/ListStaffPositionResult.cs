#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListStaffPositionResult
{
    public IReadOnlyList<StaffPositionDto> Items { get; set; } = Array.Empty<StaffPositionDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
