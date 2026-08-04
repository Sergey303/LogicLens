#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class StaffPositionDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public Guid? ParentPositionId { get; set; }
    public bool IsActive { get; set; }
}
