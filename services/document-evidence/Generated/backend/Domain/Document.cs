#nullable enable

using System.Collections.Generic;

namespace LogicLens.DocumentEvidence.Generated;

public sealed class Document
{
    public Guid Id { get; set; }
    public Guid WorkspaceId { get; set; }
    public string DisplayName { get; set; } = string.Empty;
    public string MediaType { get; set; } = string.Empty;
    public string SourceKind { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public int CurrentRevisionNumber { get; set; }
    public bool IsRevoked { get; set; }
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
    public string DisplayNameSearch { get; set; } = string.Empty;
    public string MediaTypeSearch { get; set; } = string.Empty;
    public string SourceKindSearch { get; set; } = string.Empty;
    public string StateSearch { get; set; } = string.Empty;
    public ICollection<DocumentRevision> Revisions { get; } = new List<DocumentRevision>();
}
