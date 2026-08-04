#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateDocumentRevisionRequest
{
    public Guid DocumentId { get; set; }
    public Guid StoredObjectId { get; set; }
    public int RevisionNumber { get; set; }
    [Required]
    [MaxLength(40)]
    public string State { get; set; } = string.Empty;
    [MaxLength(120)]
    public string? Adapter { get; set; }
    [MaxLength(80)]
    public string? AdapterVersion { get; set; }
    [MaxLength(64)]
    public string? ManifestHash { get; set; }
}
