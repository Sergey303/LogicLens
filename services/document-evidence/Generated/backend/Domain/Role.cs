#nullable enable

using System.Collections.Generic;

namespace LogicLens.DocumentEvidence.Generated;

public sealed class Role
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public ICollection<RolePermission> RolePermissions { get; } = new List<RolePermission>();
    public ICollection<StaffPositionRole> StaffPositionRoles { get; } = new List<StaffPositionRole>();
}
