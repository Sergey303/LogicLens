namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

public sealed record LocalObjectStoreOptions(
    string RootPath,
    string? WebRootPath = null
);
