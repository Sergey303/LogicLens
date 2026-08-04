namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public readonly record struct DocumentKey(Guid WorkspaceId, Guid DocumentId);

public sealed record DocumentSummary(
    DocumentKey Key,
    string DisplayName,
    string MediaType,
    string SourceKind,
    string State,
    int CurrentRevisionNumber,
    bool IsRevoked
);

public sealed record FragmentSummary(
    Guid FragmentId,
    Guid RevisionId,
    int Sequence,
    string Kind,
    string AnchorJson,
    string Text,
    string ContentHash
);

public sealed record GetDocumentQuery(Guid ActorId, DocumentKey Key);

public sealed record ListFragmentsQuery(
    Guid ActorId,
    Guid WorkspaceId,
    Guid RevisionId
);
