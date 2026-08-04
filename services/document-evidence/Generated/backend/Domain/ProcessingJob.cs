#nullable enable

namespace LogicLens.DocumentEvidence.Generated;

public sealed class ProcessingJob
{
    public Guid Id { get; set; }
    public Guid DocumentRevisionId { get; set; }
    public string Kind { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public int Attempt { get; set; }
    public string IdempotencyKey { get; set; } = string.Empty;
    public DateTime? LeaseUntil { get; set; }
    public string? LastErrorCode { get; set; }
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
    public string StateSearch { get; set; } = string.Empty;
    public string IdempotencyKeySearch { get; set; } = string.Empty;
    public string LastErrorCodeSearch { get; set; } = string.Empty;
    public DocumentRevision DocumentRevision { get; set; } = null!;
}
