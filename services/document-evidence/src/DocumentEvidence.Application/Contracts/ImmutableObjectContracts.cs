namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public sealed record StoredObjectReference(
    string Sha256,
    long SizeBytes,
    string ObjectKey,
    bool Created
);
