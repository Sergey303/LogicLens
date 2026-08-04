#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateDocumentFragmentRequest
{
    public Guid DocumentRevisionId { get; set; }
    public int Sequence { get; set; }
    [Required]
    [MaxLength(40)]
    public string Kind { get; set; } = string.Empty;
    [Required]
    [MaxLength(2000)]
    public string AnchorJson { get; set; } = string.Empty;
    [Required]
    [MaxLength(8000)]
    public string Text { get; set; } = string.Empty;
    [Required]
    [MaxLength(64)]
    public string ContentHash { get; set; } = string.Empty;
}
