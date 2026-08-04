#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class StoredObjectDto
{
    public Guid Id { get; set; }
    public string Sha256 { get; set; } = string.Empty;
    public string StorageKey { get; set; } = string.Empty;
    public long SizeBytes { get; set; }
    public string MediaType { get; set; } = string.Empty;
}
