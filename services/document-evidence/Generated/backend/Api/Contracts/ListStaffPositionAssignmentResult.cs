#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListStaffPositionAssignmentResult
{
    public IReadOnlyList<StaffPositionAssignmentDto> Items { get; set; } = Array.Empty<StaffPositionAssignmentDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
