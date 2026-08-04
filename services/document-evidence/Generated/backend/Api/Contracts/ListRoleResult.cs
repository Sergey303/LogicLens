#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ListRoleResult
{
    public IReadOnlyList<RoleDto> Items { get; set; } = Array.Empty<RoleDto>();

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}
