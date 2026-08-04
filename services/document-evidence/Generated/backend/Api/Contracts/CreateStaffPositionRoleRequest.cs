#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateStaffPositionRoleRequest
{
    public Guid StaffPositionId { get; set; }
    public Guid RoleId { get; set; }
}
