namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

internal sealed class GeneratedDocumentDto
{
    public Guid Id { get; init; }

    public Guid WorkspaceId { get; init; }

    public string DisplayName { get; init; } = string.Empty;

    public string MediaType { get; init; } = string.Empty;

    public string SourceKind { get; init; } = string.Empty;

    public string State { get; init; } = string.Empty;

    public int CurrentRevisionNumber { get; init; }

    public bool IsRevoked { get; init; }
}

internal sealed class GeneratedDocumentRevisionDto
{
    public Guid Id { get; init; }

    public Guid DocumentId { get; init; }
}

internal sealed class GeneratedDocumentFragmentDto
{
    public Guid Id { get; init; }

    public Guid DocumentRevisionId { get; init; }

    public int Sequence { get; init; }

    public string Kind { get; init; } = string.Empty;

    public string AnchorJson { get; init; } = string.Empty;

    public string Text { get; init; } = string.Empty;

    public string ContentHash { get; init; } = string.Empty;
}

internal sealed class GeneratedListResult<T>
{
    public List<T> Items { get; init; } = [];

    public int Page { get; init; }

    public int PageSize { get; init; }

    public int TotalCount { get; init; }
}
