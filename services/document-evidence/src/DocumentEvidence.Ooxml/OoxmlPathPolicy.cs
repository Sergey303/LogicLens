namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

internal static class OoxmlPathPolicy
{
    public static string DemandPartName(string name)
    {
        if (string.IsNullOrWhiteSpace(name)
            || name.StartsWith("/", StringComparison.Ordinal)
            || name.Contains('\\', StringComparison.Ordinal)
            || name.Contains(':', StringComparison.Ordinal))
        {
            throw new InvalidDataException($"Unsafe OOXML part name: {name}");
        }
        var segments = name.Split('/');
        if (segments.Any(segment =>
            segment.Length == 0
            || segment is "." or ".."
            || segment.Any(char.IsControl)))
        {
            throw new InvalidDataException($"Unsafe OOXML part name: {name}");
        }
        return name;
    }

    public static string ResolveInternalTarget(string sourcePart, string target)
    {
        var normalized = target.Trim();
        var packageAbsolute = normalized.StartsWith("/", StringComparison.Ordinal);
        if (normalized.Length == 0
            || normalized.StartsWith("//", StringComparison.Ordinal)
            || normalized.Contains("//", StringComparison.Ordinal)
            || normalized.Contains('\\', StringComparison.Ordinal)
            || (!packageAbsolute && Uri.TryCreate(normalized, UriKind.Absolute, out _)))
        {
            throw new InvalidDataException($"Unsafe OOXML relationship target: {target}");
        }
        var targetPath = packageAbsolute ? normalized[1..] : normalized;
        if (targetPath.Length == 0)
        {
            throw new InvalidDataException($"Unsafe OOXML relationship target: {target}");
        }
        var baseSegments = packageAbsolute
            ? new List<string>()
            : sourcePart.Split('/').SkipLast(1).ToList();
        foreach (var segment in targetPath.Split('/'))
        {
            if (segment == ".")
            {
                continue;
            }
            if (segment == "..")
            {
                if (baseSegments.Count == 0)
                {
                    throw new InvalidDataException("OOXML relationship escapes package root.");
                }
                baseSegments.RemoveAt(baseSegments.Count - 1);
                continue;
            }
            if (segment.Length == 0)
            {
                throw new InvalidDataException($"Unsafe OOXML relationship target: {target}");
            }
            baseSegments.Add(segment);
        }
        return DemandPartName(string.Join('/', baseSegments));
    }
}
