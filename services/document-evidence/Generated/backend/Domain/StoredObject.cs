#nullable enable

using System.Collections.Generic;

namespace LogicLens.DocumentEvidence.Generated;

public sealed class StoredObject
{
    public Guid Id { get; set; }
    public string Sha256 { get; set; } = string.Empty;
    public string StorageKey { get; set; } = string.Empty;
    public long SizeBytes { get; set; }
    public string MediaType { get; set; } = string.Empty;
    public DateTime CreationTime { get; set; }
    public Guid? CreatorId { get; set; }
    public Guid? CreatorPositionId { get; set; }
    public DateTime? LastModificationTime { get; set; }
    public Guid? LastModifierId { get; set; }
    public Guid? LastModifierPositionId { get; set; }
    public bool IsDeleted { get; set; }
    public DateTime? DeletionTime { get; set; }
    public Guid? DeleterId { get; set; }
    public Guid? DeleterPositionId { get; set; }
    public string Sha256Search { get; set; } = string.Empty;
    public string StorageKeySearch { get; set; } = string.Empty;
    public string MediaTypeSearch { get; set; } = string.Empty;
    public ICollection<DocumentRevision> Revisions { get; } = new List<DocumentRevision>();
}
