using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;

namespace LogicLens.Ui.Mapping;

public sealed class GenericUiDocumentMapper
{
    public JsonObject MapEntityView(
        JsonObject response,
        string requestedEntityId,
        string language)
    {
        ArgumentNullException.ThrowIfNull(response);
        ArgumentException.ThrowIfNullOrWhiteSpace(requestedEntityId);

        var epoch = RequiredInt(response, "epoch");
        var revision = RequiredInt(response, "revision");
        var result = RequiredObject(response, "result");
        var view = RequiredObject(result, "view");
        var entityId = RequiredString(view, "entity");
        if (!StringComparer.Ordinal.Equals(entityId, requestedEntityId))
        {
            throw new InvalidDataException(
                "Prolog entity-view returned a different entity identifier.");
        }

        var title = RequiredString(view, "title");
        var groups = RequiredArray(view, "groups");
        var normal = new JsonArray();
        var technical = new JsonArray();

        foreach (var node in groups)
        {
            var group = node as JsonObject
                ?? throw new InvalidDataException("Entity-view group must be an object.");
            var property = MapGroup(group);
            if (RequiredBool(group, "technical"))
            {
                technical.Add(property);
            }
            else
            {
                normal.Add(property);
            }
        }

        var sections = new JsonArray();
        if (normal.Count > 0)
        {
            sections.Add(CreateSection(
                "section:properties",
                Localized(language, "Свойства", "Properties"),
                "default",
                normal));
        }

        if (technical.Count > 0)
        {
            sections.Add(CreateSection(
                "section:technical",
                Localized(language, "Технические данные", "Technical data"),
                "technical",
                technical));
        }

        var rawProlog = result["rawProlog"]?.GetValue<string?>();
        if (rawProlog is not null)
        {
            sections.Add(CreateSection(
                "section:raw-prolog",
                Localized(language, "Prolog", "Prolog"),
                "technical",
                new JsonArray
                {
                    new JsonObject
                    {
                        ["kind"] = "rawProlog",
                        ["id"] = "raw-prolog:entity",
                        ["title"] = Localized(
                            language,
                            "Базовые факты Prolog",
                            "Base Prolog facts"),
                        ["code"] = rawProlog,
                        ["artifactKind"] = "data"
                    }
                }));
        }

        var diagnostics = new JsonArray();
        AppendDiagnostics(response["diagnostics"] as JsonArray, diagnostics, "cli");
        AppendDiagnostics(view["diagnostics"] as JsonArray, diagnostics, "view");

        return new JsonObject
        {
            ["schemaVersion"] = "0.1",
            ["epoch"] = epoch,
            ["revision"] = revision,
            ["context"] = new JsonObject
            {
                ["kind"] = "entity",
                ["entityId"] = entityId
            },
            ["page"] = new JsonObject
            {
                ["kind"] = "page",
                ["id"] = ComponentId("page", entityId),
                ["title"] = title,
                ["sections"] = sections
            },
            ["diagnostics"] = diagnostics
        };
    }

    public static JsonObject CreateDiagnostic(
        string code,
        string severity,
        string message) =>
        new()
        {
            ["kind"] = "diagnostic",
            ["id"] = ComponentId("diagnostic", code + "\0" + message),
            ["severity"] = severity,
            ["message"] = message
        };

    private static JsonObject MapGroup(JsonObject group)
    {
        var direction = RequiredString(group, "direction");
        var predicate = RequiredString(group, "predicate");
        var values = RequiredArray(group, "values");
        if (values.Count == 0)
        {
            throw new InvalidDataException("Entity-view group cannot be empty.");
        }

        var mappedValues = new JsonArray();
        foreach (var node in values)
        {
            mappedValues.Add(MapValue(
                node as JsonObject
                    ?? throw new InvalidDataException("Entity-view value must be an object.")));
        }

        return new JsonObject
        {
            ["kind"] = "property",
            ["id"] = ComponentId("property", direction + "\0" + predicate),
            ["predicate"] = predicate,
            ["label"] = RequiredString(group, "label"),
            ["direction"] = direction,
            ["values"] = mappedValues
        };
    }

    private static JsonObject MapValue(JsonObject value)
    {
        var kind = RequiredString(value, "kind");
        var mapped = kind switch
        {
            "text" => new JsonObject
            {
                ["kind"] = "text",
                ["text"] = RequiredStringAllowEmpty(value, "text"),
                ["literalKind"] = RequiredString(value, "literalKind"),
                ["language"] = Clone(value["language"]),
                ["datatype"] = Clone(value["datatype"]),
                ["editable"] = true
            },
            "resourceLink" => new JsonObject
            {
                ["kind"] = "resourceLink",
                ["targetId"] = RequiredString(value, "targetId"),
                ["label"] = RequiredStringAllowEmpty(value, "label"),
                ["editable"] = true
            },
            _ => throw new InvalidDataException(
                $"Unsupported entity-view value kind '{kind}'.")
        };
        mapped["source"] = MapBaseSource(RequiredObject(value, "source"));
        return mapped;
    }

    private static JsonObject MapBaseSource(JsonObject source)
    {
        if (!StringComparer.Ordinal.Equals(RequiredString(source, "kind"), "base"))
        {
            throw new InvalidDataException("Generic entity-view values must have base sources.");
        }

        return new JsonObject
        {
            ["kind"] = "base",
            ["fact"] = new JsonObject
            {
                ["factId"] = RequiredString(source, "factId"),
                ["subject"] = RequiredString(source, "subject"),
                ["predicate"] = RequiredString(source, "predicate"),
                ["object"] = MapFactObject(RequiredObject(source, "object"))
            },
            ["origins"] = Clone(RequiredArray(source, "origins"))
        };
    }

    private static JsonObject MapFactObject(JsonObject value)
    {
        var kind = RequiredString(value, "kind");
        return kind switch
        {
            "iri" => new JsonObject
            {
                ["kind"] = "iri",
                ["resourceId"] = RequiredString(value, "value")
            },
            "literal" => new JsonObject
            {
                ["kind"] = "literal",
                ["lexical"] = RequiredStringAllowEmpty(value, "lexical"),
                ["literalKind"] = RequiredString(value, "literalKind"),
                ["language"] = Clone(value["language"]),
                ["datatype"] = Clone(value["datatype"])
            },
            _ => throw new InvalidDataException(
                $"Unsupported canonical object kind '{kind}'.")
        };
    }

    private static JsonObject CreateSection(
        string id,
        string title,
        string presentation,
        JsonArray components) =>
        new()
        {
            ["kind"] = "section",
            ["id"] = id,
            ["title"] = title,
            ["presentation"] = presentation,
            ["components"] = components
        };

    private static void AppendDiagnostics(
        JsonArray? source,
        JsonArray destination,
        string prefix)
    {
        if (source is null)
        {
            return;
        }

        var index = 0;
        foreach (var node in source)
        {
            var diagnostic = node as JsonObject
                ?? throw new InvalidDataException("Diagnostic must be an object.");
            destination.Add(CreateDiagnostic(
                prefix + ":" + index + ":" + RequiredString(diagnostic, "code"),
                RequiredString(diagnostic, "severity"),
                RequiredString(diagnostic, "message")));
            index++;
        }
    }

    private static string ComponentId(string prefix, string source)
    {
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(source));
        return prefix + ":" + Convert.ToHexString(hash[..12]).ToLowerInvariant();
    }

    private static string Localized(
        string language,
        string russian,
        string english) =>
        language.StartsWith("ru", StringComparison.OrdinalIgnoreCase)
            ? russian
            : english;

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

    private static int RequiredInt(JsonObject parent, string name) =>
        parent[name]?.GetValue<int>()
        ?? throw new InvalidDataException($"Required integer '{name}' is missing.");

    private static bool RequiredBool(JsonObject parent, string name) =>
        parent[name]?.GetValue<bool>()
        ?? throw new InvalidDataException($"Required boolean '{name}' is missing.");

    private static JsonNode? Clone(JsonNode? value) => value?.DeepClone();
}
