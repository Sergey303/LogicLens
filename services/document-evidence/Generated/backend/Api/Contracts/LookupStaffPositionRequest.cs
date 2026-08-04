#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class LookupStaffPositionRequest
{
    public string? Query { get; set; }
    public int Take { get; set; } = 10;
}
