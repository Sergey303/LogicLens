#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class ProcessingJobDto
{
    public Guid Id { get; set; }
    public Guid DocumentRevisionId { get; set; }
    public string Kind { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public int Attempt { get; set; }
    public string IdempotencyKey { get; set; } = string.Empty;
    public DateTime? LeaseUntil { get; set; }
    public string? LastErrorCode { get; set; }
}
