#nullable enable

using System.Collections.Generic;

namespace LogicLens.DocumentEvidence.Generated;

public sealed class DocumentRevision
{
    public Guid Id { get; set; }
    public Guid DocumentId { get; set; }
    public Guid StoredObjectId { get; set; }
    public int RevisionNumber { get; set; }
    public string State { get; set; } = string.Empty;
    public string? Adapter { get; set; }
    public string? AdapterVersion { get; set; }
    public string? ManifestHash { get; set; }
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
    public string StateSearch { get; set; } = string.Empty;
    public string AdapterSearch { get; set; } = string.Empty;
    public string AdapterVersionSearch { get; set; } = string.Empty;
    public string ManifestHashSearch { get; set; } = string.Empty;
    public Document Document { get; set; } = null!;
    public StoredObject StoredObject { get; set; } = null!;
    public ICollection<ProcessingJob> ProcessingJobs { get; } = new List<ProcessingJob>();
    public ICollection<DocumentFragment> Fragments { get; } = new List<DocumentFragment>();
}
