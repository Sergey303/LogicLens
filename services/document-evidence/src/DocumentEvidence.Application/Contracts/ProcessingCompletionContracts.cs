namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public sealed record ProcessingArtifactManifest(
    string Adapter,
    string AdapterVersion,
    string ConfigurationSha256,
    string ArtifactSha256,
    string IrSha256,
    string ManifestJson,
    string ManifestSha256
);

public sealed record ProcessingFragmentWrite(
    Guid FragmentId,
    Guid RevisionId,
    int Sequence,
    string Kind,
    string AnchorJson,
    string Text,
    string ContentHash
);

public sealed record ProcessingCompletionPayload(
    Guid RevisionId,
    DateTimeOffset CompletedAt,
    ProcessingArtifactManifest Manifest,
    IReadOnlyList<ProcessingFragmentWrite> Fragments
);
