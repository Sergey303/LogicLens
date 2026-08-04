#nullable enable

namespace LogicLens.DocumentEvidence.Generated;

public sealed class StaffPositionRole
{
    public Guid Id { get; set; }
    public Guid StaffPositionId { get; set; }
    public Guid RoleId { get; set; }
    public StaffPosition StaffPosition { get; set; } = null!;
    public Role Role { get; set; } = null!;
}
