#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class DocumentDto
{
    public Guid Id { get; set; }
    public Guid WorkspaceId { get; set; }
    public string DisplayName { get; set; } = string.Empty;
    public string MediaType { get; set; } = string.Empty;
    public string SourceKind { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public int CurrentRevisionNumber { get; set; }
    public bool IsRevoked { get; set; }
}
