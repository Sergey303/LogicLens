namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

internal sealed class LocalStoragePaths
{
    private readonly StringComparison _comparison;
    private readonly string _objectsRoot;
    private readonly string _root;

    public LocalStoragePaths(LocalObjectStoreOptions options)
    {
        ArgumentNullException.ThrowIfNull(options);
        ArgumentException.ThrowIfNullOrWhiteSpace(options.RootPath);

        _comparison = OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;
        _root = Path.GetFullPath(options.RootPath);
        if (!string.IsNullOrWhiteSpace(options.WebRootPath))
        {
            var webRoot = Path.GetFullPath(options.WebRootPath);
            if (PathsOverlap(_root, webRoot))
            {
                throw new ArgumentException(
                    "Object storage root must not overlap the configured web root.",
                    nameof(options)
                );
            }
        }

        _objectsRoot = DemandInsideRoot(Path.Combine(_root, "objects", "sha256"));
        StagingRoot = DemandInsideRoot(Path.Combine(_root, ".staging"));
        Directory.CreateDirectory(_objectsRoot);
        Directory.CreateDirectory(StagingRoot);
    }

    public string StagingRoot { get; }

    public ObjectAddress Resolve(string sha256)
    {
        var normalized = NormalizeSha256(sha256);
        var objectKey = $"sha256/{normalized[..2]}/{normalized[2..4]}/{normalized}";
        var objectPath = DemandInsideRoot(
            Path.Combine(_objectsRoot, normalized[..2], normalized[2..4], normalized)
        );
        return new ObjectAddress(normalized, objectKey, objectPath);
    }

    public string CreateStagingPath()
    {
        return DemandInsideRoot(Path.Combine(StagingRoot, $"{Guid.NewGuid():N}.upload"));
    }

    private string DemandInsideRoot(string path)
    {
        var fullPath = Path.GetFullPath(path);
        if (!IsWithin(fullPath, _root))
        {
            throw new InvalidDataException("Resolved local storage path escaped its configured root.");
        }
        return fullPath;
    }

    private bool PathsOverlap(string first, string second)
    {
        return IsWithin(first, second) || IsWithin(second, first);
    }

    private bool IsWithin(string candidate, string parent)
    {
        if (string.Equals(candidate, parent, _comparison))
        {
            return true;
        }
        var prefix = parent.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        return candidate.StartsWith(prefix, _comparison);
    }

    private static string NormalizeSha256(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        if (value.Length != 64 || value.Any(character => !Uri.IsHexDigit(character)))
        {
            throw new ArgumentException("Object hash must be a 64-character SHA-256 hex value.", nameof(value));
        }
        return value.ToLowerInvariant();
    }
}

internal sealed record ObjectAddress(
    string Sha256,
    string ObjectKey,
    string ObjectPath
);
