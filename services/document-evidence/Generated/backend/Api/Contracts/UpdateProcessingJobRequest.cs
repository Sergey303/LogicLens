#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class UpdateProcessingJobRequest
{
    public Guid DocumentRevisionId { get; set; }
    [Required]
    [MaxLength(80)]
    public string Kind { get; set; } = string.Empty;
    [Required]
    [MaxLength(40)]
    public string State { get; set; } = string.Empty;
    public int Attempt { get; set; }
    [Required]
    [MaxLength(160)]
    public string IdempotencyKey { get; set; } = string.Empty;
    public DateTime? LeaseUntil { get; set; }
    [MaxLength(120)]
    public string? LastErrorCode { get; set; }
}
