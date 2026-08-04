#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateStaffPositionRequest
{
    [Required]
    [MaxLength(128)]
    public string Code { get; set; } = string.Empty;
    [Required]
    [MaxLength(200)]
    public string Name { get; set; } = string.Empty;
    [MaxLength(1000)]
    public string? Description { get; set; }
    public Guid? ParentPositionId { get; set; }
    public bool IsActive { get; set; }
}
