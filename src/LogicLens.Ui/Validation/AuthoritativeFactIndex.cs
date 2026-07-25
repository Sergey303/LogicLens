using System.Text.Json.Nodes;

namespace LogicLens.Ui.Validation;

internal sealed record AuthoritativeFact(
    string FactId,
    string Subject,
    string Predicate,
    JsonObject Object,
    IReadOnlyList<string> Origins);

internal sealed class AuthoritativeFactIndex
{
    private readonly IReadOnlyDictionary<string, AuthoritativeFact> facts;

    private AuthoritativeFactIndex(
        IReadOnlyDictionary<string, AuthoritativeFact> facts,
        IReadOnlySet<string> nodes)
    {
        this.facts = facts;
        Nodes = nodes;
    }

    public IReadOnlySet<string> Nodes { get; }

    public IReadOnlyCollection<string> FactIds => facts.Keys;

    public bool TryGet(string factId, out AuthoritativeFact fact) =>
        facts.TryGetValue(factId, out fact!);

    public static AuthoritativeFactIndex Build(JsonArray source)
    {
        ArgumentNullException.ThrowIfNull(source);
        var facts = new Dictionary<string, AuthoritativeFact>(StringComparer.Ordinal);
        var nodes = new HashSet<string>(StringComparer.Ordinal);

        foreach (var node in source)
        {
            var value = node as JsonObject
                ?? throw new InvalidDataException("Authoritative fact must be an object.");
            var factId = RequiredString(value, "factId");
            var subject = RequiredString(value, "subject");
            var predicate = RequiredString(value, "predicate");
            var factObject = NormalizeObject(RequiredObject(value, "object"));
            var origins = RequiredArray(value, "origins")
                .Select(static item => item?.GetValue<string>()
                    ?? throw new InvalidDataException("Origin identifier is missing."))
                .OrderBy(static item => item, StringComparer.Ordinal)
                .ToArray();
            if (origins.Length == 0 || origins.Distinct(StringComparer.Ordinal).Count() != origins.Length)
            {
                throw new InvalidDataException(
                    $"Authoritative fact '{factId}' has invalid origins.");
            }

            var fact = new AuthoritativeFact(
                factId,
                subject,
                predicate,
                factObject,
                origins);
            if (!facts.TryAdd(factId, fact))
            {
                throw new InvalidDataException(
                    $"Duplicate authoritative FactId '{factId}'.");
            }

            nodes.Add(subject);
            if (StringComparer.Ordinal.Equals(RequiredString(factObject, "kind"), "iri"))
            {
                nodes.Add(RequiredString(factObject, "resourceId"));
            }
        }

        return new AuthoritativeFactIndex(facts, nodes);
    }

    public static bool JsonEqual(JsonNode? first, JsonNode? second) =>
        JsonNode.DeepEquals(first, second);

    private static JsonObject NormalizeObject(JsonObject source)
    {
        var kind = RequiredString(source, "kind");
        return kind switch
        {
            "iri" => new JsonObject
            {
                ["kind"] = "iri",
                ["resourceId"] = RequiredString(source, "value")
            },
            "literal" => new JsonObject
            {
                ["kind"] = "literal",
                ["lexical"] = RequiredStringAllowEmpty(source, "lexical"),
                ["literalKind"] = RequiredString(source, "literalKind"),
                ["language"] = source["language"]?.DeepClone(),
                ["datatype"] = source["datatype"]?.DeepClone()
            },
            _ => throw new InvalidDataException(
                $"Unsupported authoritative object kind '{kind}'.")
        };
    }

    private static JsonObject RequiredObject(JsonObject parent, string name) =>
        parent[name] as JsonObject
        ?? throw new InvalidDataException($"Required object '{name}' is missing.");

    private static JsonArray RequiredArray(JsonObject parent, string name) =>
        parent[name] as JsonArray
        ?? throw new InvalidDataException($"Required array '{name}' is missing.");

    private static string RequiredString(JsonObject parent, string name)
    {
        var value = RequiredStringAllowEmpty(parent, name);
        return value.Length > 0
            ? value
            : throw new InvalidDataException($"Required string '{name}' is empty.");
    }

    private static string RequiredStringAllowEmpty(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>()
        ?? throw new InvalidDataException($"Required string '{name}' is missing.");
}
