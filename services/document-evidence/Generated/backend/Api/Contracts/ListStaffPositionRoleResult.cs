#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListStaffPositionRoleResult
{
    public IReadOnlyList<StaffPositionRoleDto> Items { get; set; } = Array.Empty<StaffPositionRoleDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
