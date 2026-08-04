#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListRolePermissionResult
{
    public IReadOnlyList<RolePermissionDto> Items { get; set; } = Array.Empty<RolePermissionDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
