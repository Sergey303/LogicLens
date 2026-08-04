#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class DocumentRevisionDto
{
    public Guid Id { get; set; }
    public Guid DocumentId { get; set; }
    public Guid StoredObjectId { get; set; }
    public int RevisionNumber { get; set; }
    public string State { get; set; } = string.Empty;
    public string? Adapter { get; set; }
    public string? AdapterVersion { get; set; }
    public string? ManifestHash { get; set; }
}
