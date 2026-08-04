#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class DocumentFragmentDto
{
    public Guid Id { get; set; }
    public Guid DocumentRevisionId { get; set; }
    public int Sequence { get; set; }
    public string Kind { get; set; } = string.Empty;
    public string AnchorJson { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string ContentHash { get; set; } = string.Empty;
}
