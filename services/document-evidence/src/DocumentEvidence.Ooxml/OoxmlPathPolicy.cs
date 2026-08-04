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
        if (string.IsNullOrWhiteSpace(target)
            || target.StartsWith("/", StringComparison.Ordinal)
            || target.Contains('\\', StringComparison.Ordinal)
            || Uri.TryCreate(target, UriKind.Absolute, out _))
        {
            throw new InvalidDataException($"Unsafe OOXML relationship target: {target}");
        }
        var baseSegments = sourcePart.Split('/').SkipLast(1).ToList();
        foreach (var segment in target.Split('/'))
        {
            if (segment is "" or ".")
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
            baseSegments.Add(segment);
        }
        return DemandPartName(string.Join('/', baseSegments));
    }
}
