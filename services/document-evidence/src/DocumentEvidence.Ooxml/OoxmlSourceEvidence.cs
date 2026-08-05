using System.Text.Json;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public sealed record OoxmlSelectedFragment(
    string StableId,
    string Kind,
    string Text,
    string ContentSha256,
    JsonElement SourceAnchor,
    IReadOnlyList<string> HeadingPath
);

public sealed record RetainedOoxmlEvidence(
    string SourceId,
    string ArtifactSha256,
    string AdapterName,
    string AdapterVersion,
    IReadOnlyList<OoxmlSelectedFragment> Fragments
);
