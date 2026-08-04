namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public sealed record OoxmlPackageLimits(
    long MaxPackageBytes = 67_108_864,
    int MaxEntries = 2_048,
    long MaxEntryBytes = 67_108_864,
    long MaxUncompressedBytes = 268_435_456
);

public sealed record OoxmlCoreProperties(
    string? Title,
    string? Subject,
    string? Creator,
    string? Description,
    string? CreatedUtc,
    string? ModifiedUtc
);

public sealed record OoxmlPackageIdentity(
    string ArtifactSha256,
    string EntriesSha256,
    int EntryCount,
    long UncompressedBytes,
    OoxmlCoreProperties CoreProperties
);

public sealed record OoxmlPart(
    string Name,
    byte[] Content,
    string ContentSha256
);

public sealed class OoxmlPackageSnapshot
{
    private readonly IReadOnlyDictionary<string, OoxmlPart> _parts;

    internal OoxmlPackageSnapshot(
        OoxmlPackageIdentity identity,
        IReadOnlyDictionary<string, OoxmlPart> parts
    )
    {
        Identity = identity;
        _parts = parts;
    }

    public OoxmlPackageIdentity Identity { get; }
    public IReadOnlyCollection<string> PartNames => _parts.Keys;

    public OoxmlPart RequirePart(string name) =>
        _parts.TryGetValue(name, out var part)
            ? part
            : throw new InvalidDataException($"Required OOXML part is missing: {name}");

    public OoxmlPart? FindPart(string name) => _parts.GetValueOrDefault(name);
}
