#nullable enable

using System.Collections.Generic;

namespace LogicLens.DocumentEvidence.Generated;

public sealed class StaffPosition
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public Guid? ParentPositionId { get; set; }
    public bool IsActive { get; set; }
    public StaffPosition? ParentPosition { get; set; }
    public ICollection<StaffPosition> ChildPositions { get; } = new List<StaffPosition>();
    public ICollection<StaffPositionRole> StaffPositionRoles { get; } = new List<StaffPositionRole>();
    public ICollection<StaffPositionAssignment> StaffPositionAssignments { get; } = new List<StaffPositionAssignment>();
}
