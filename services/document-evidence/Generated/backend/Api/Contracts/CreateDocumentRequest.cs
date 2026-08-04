#nullable enable

using System.ComponentModel.DataAnnotations;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class CreateDocumentRequest
{
    public Guid WorkspaceId { get; set; }
    [Required]
    [MaxLength(260)]
    public string DisplayName { get; set; } = string.Empty;
    [Required]
    [MaxLength(120)]
    public string MediaType { get; set; } = string.Empty;
    [Required]
    [MaxLength(40)]
    public string SourceKind { get; set; } = string.Empty;
    [Required]
    [MaxLength(40)]
    public string State { get; set; } = string.Empty;
    public int CurrentRevisionNumber { get; set; }
    public bool IsRevoked { get; set; }
}
