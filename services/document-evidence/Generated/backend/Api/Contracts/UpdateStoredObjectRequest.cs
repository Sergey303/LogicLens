#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class UpdateStoredObjectRequest
{
    [Required]
    [MaxLength(64)]
    public string Sha256 { get; set; } = string.Empty;
    [Required]
    [MaxLength(512)]
    public string StorageKey { get; set; } = string.Empty;
    public long SizeBytes { get; set; }
    [Required]
    [MaxLength(120)]
    public string MediaType { get; set; } = string.Empty;
}
