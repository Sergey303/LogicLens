#nullable enable

namespace LogicLens.DocumentEvidence.Generated;

public sealed class DocumentFragment
{
    public Guid Id { get; set; }
    public Guid DocumentRevisionId { get; set; }
    public int Sequence { get; set; }
    public string Kind { get; set; } = string.Empty;
    public string AnchorJson { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string ContentHash { get; set; } = string.Empty;
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
    public string KindSearch { get; set; } = string.Empty;
    public string AnchorJsonSearch { get; set; } = string.Empty;
    public string TextSearch { get; set; } = string.Empty;
    public string ContentHashSearch { get; set; } = string.Empty;
    public DocumentRevision DocumentRevision { get; set; } = null!;
}
