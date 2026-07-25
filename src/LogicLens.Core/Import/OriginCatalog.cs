using System.Text.Json;
using LogicLens.Core.Model;

namespace LogicLens.Core.Import;

public sealed class OriginCatalog
{
    private readonly Dictionary<(string SourcePath, string EntityId), Origin> _origins;

    private OriginCatalog(
        Dictionary<(string SourcePath, string EntityId), Origin> origins)
    {
        _origins = origins;
    }

    public int Count => _origins.Count;

    public static OriginCatalog LoadJson(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);

        using var stream = File.OpenRead(path);
        using var document = JsonDocument.Parse(stream, new JsonDocumentOptions
        {
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow
        });

        var root = document.RootElement;
        EnsureObjectProperties(root, path, "origins");
        var originsElement = root.GetProperty("origins");
        if (originsElement.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidDataException($"{path}: 'origins' must be an array.");
        }

        var origins = new Dictionary<(string SourcePath, string EntityId), Origin>();
        var originIds = new HashSet<string>(StringComparer.Ordinal);

        foreach (var element in originsElement.EnumerateArray())
        {
            EnsureObjectProperties(
                element,
                path,
                "originId",
                "sourcePath",
                "sourceDbId",
                "entityId");

            var origin = new Origin(
                RequiredString(element, "originId", path),
                RequiredString(element, "sourcePath", path),
                RequiredString(element, "sourceDbId", path),
                RequiredString(element, "entityId", path));

            if (!originIds.Add(origin.OriginId))
            {
                throw new InvalidDataException(
                    $"{path}: duplicate OriginId '{origin.OriginId}'.");
            }

            var key = (origin.SourcePath, origin.EntityId);
            if (!origins.TryAdd(key, origin))
            {
                throw new InvalidDataException(
                    $"{path}: duplicate source/entity origin key '{key}'.");
            }
        }

        return new OriginCatalog(origins);
    }

    public Origin Resolve(FogOriginContext context)
    {
        ArgumentNullException.ThrowIfNull(context);

        var key = (context.SourcePath, context.EntityId);
        if (!_origins.TryGetValue(key, out var origin))
        {
            throw new InvalidDataException(
                $"Origin catalog has no entry for source '{context.SourcePath}' " +
                $"and entity '{context.EntityId}'.");
        }

        if (!StringComparer.Ordinal.Equals(origin.SourceDbId, context.SourceDbId))
        {
            throw new InvalidDataException(
                $"Origin '{origin.OriginId}' expects dbid '{origin.SourceDbId}', " +
                $"but FOG contains '{context.SourceDbId}'.");
        }

        return origin;
    }

    private static string RequiredString(
        JsonElement element,
        string propertyName,
        string path)
    {
        if (!element.TryGetProperty(propertyName, out var property)
            || property.ValueKind != JsonValueKind.String)
        {
            throw new InvalidDataException(
                $"{path}: '{propertyName}' must be a string.");
        }

        var value = property.GetString();
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException(
                $"{path}: '{propertyName}' cannot be empty.");
        }

        return value;
    }

    private static void EnsureObjectProperties(
        JsonElement element,
        string path,
        params string[] allowedProperties)
    {
        if (element.ValueKind != JsonValueKind.Object)
        {
            throw new InvalidDataException($"{path}: expected a JSON object.");
        }

        var allowed = allowedProperties.ToHashSet(StringComparer.Ordinal);
        foreach (var property in element.EnumerateObject())
        {
            if (!allowed.Contains(property.Name))
            {
                throw new InvalidDataException(
                    $"{path}: unsupported property '{property.Name}'.");
            }
        }

        foreach (var required in allowedProperties)
        {
            if (!element.TryGetProperty(required, out _))
            {
                throw new InvalidDataException(
                    $"{path}: required property '{required}' is missing.");
            }
        }
    }
}
