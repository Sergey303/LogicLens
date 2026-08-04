#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateRolePermissionRequest
{
    public Guid RoleId { get; set; }
    public Guid PermissionId { get; set; }
}
