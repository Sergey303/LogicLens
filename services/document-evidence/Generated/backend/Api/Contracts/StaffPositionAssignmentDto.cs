#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class StaffPositionAssignmentDto
{
    public Guid Id { get; set; }
    public Guid StaffPositionId { get; set; }
    public Guid UserId { get; set; }
    public string AssignmentKind { get; set; } = string.Empty;
    public DateTime StartsAt { get; set; }
    public DateTime? EndsAt { get; set; }
    public DateTime StartsAtUtc { get; set; }
    public DateTime? EndsAtUtc { get; set; }
    public bool IsActive { get; set; }
    public string? Reason { get; set; }
}
