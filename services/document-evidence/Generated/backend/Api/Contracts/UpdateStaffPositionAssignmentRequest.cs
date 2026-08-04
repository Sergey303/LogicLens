#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class UpdateStaffPositionAssignmentRequest
{
    public Guid StaffPositionId { get; set; }
    public Guid UserId { get; set; }
    [Required]
    [MaxLength(32)]
    public string AssignmentKind { get; set; } = string.Empty;
    public DateTime StartsAt { get; set; }
    public DateTime? EndsAt { get; set; }
    public DateTime StartsAtUtc { get; set; }
    public DateTime? EndsAtUtc { get; set; }
    public bool IsActive { get; set; }
    [MaxLength(500)]
    public string? Reason { get; set; }
}
