using System.Globalization;
using System.Text.Json;
using LogicLens.Core.Model;

namespace LogicLens.State;

internal sealed record LoggedAdd(
    CanonicalFact Fact,
    EditRuntimeFactOrigin Origin);

internal sealed record RuntimeLogRecord(
    string SnapshotId,
    string CommandId,
    string RequestHash,
    string Actor,
    DateTimeOffset AcceptedAtUtc,
    long BeforeRevision,
    long AfterRevision,
    IReadOnlyList<LoggedAdd> Add,
    IReadOnlyList<string> Delete)
{
    public bool Changed => Add.Count > 0 || Delete.Count > 0;

    public ApplyDeltaResult ToResult() => new(
        CommandId,
        RequestHash,
        BeforeRevision,
        AfterRevision,
        Changed,
        Add.Select(static item => item.Fact.FactId).ToArray(),
        Delete.ToArray(),
        AcceptedAtUtc);

    public static RuntimeLogRecord Create(
        string snapshotId,
        ApplyDeltaCommand command,
        string requestHash,
        long beforeRevision,
        DateTimeOffset acceptedAtUtc,
        IReadOnlyList<CanonicalFact> add,
        IReadOnlyList<string> delete)
    {
        var sortedAdd = add
            .OrderBy(static fact => fact.FactId, StringComparer.Ordinal)
            .Select(fact => new LoggedAdd(
                fact,
                new EditRuntimeFactOrigin(
                    EditOriginId(command.CommandId, fact.FactId),
                    command.Actor,
                    command.CommandId,
                    acceptedAtUtc)))
            .ToArray();
        var sortedDelete = delete
            .OrderBy(static factId => factId, StringComparer.Ordinal)
            .ToArray();
        var changed = sortedAdd.Length > 0 || sortedDelete.Length > 0;
        return new RuntimeLogRecord(
            snapshotId,
            command.CommandId,
            requestHash,
            command.Actor,
            acceptedAtUtc.ToUniversalTime(),
            beforeRevision,
            changed ? checked(beforeRevision + 1) : beforeRevision,
            sortedAdd,
            sortedDelete);
    }

    public static string EditOriginId(string commandId, string factId) =>
        "edit:" + commandId + ":" + factId;
}

internal static class RuntimeLogRecordJson
{
    public static byte[] Serialize(RuntimeLogRecord record)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(
                   stream,
                   new JsonWriterOptions { Indented = false }))
        {
            writer.WriteStartObject();
            writer.WriteNumber("formatVersion", 1);
            writer.WriteString("snapshotId", record.SnapshotId);
            writer.WriteString("commandId", record.CommandId);
            writer.WriteString("requestHash", record.RequestHash);
            writer.WriteString("actor", record.Actor);
            writer.WriteString(
                "acceptedAtUtc",
                record.AcceptedAtUtc.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture));
            writer.WriteNumber("beforeRevision", record.BeforeRevision);
            writer.WriteNumber("afterRevision", record.AfterRevision);
            writer.WriteStartArray("add");
            foreach (var item in record.Add)
            {
                writer.WriteStartObject();
                writer.WriteString("factId", item.Fact.FactId);
                writer.WriteString("subject", item.Fact.Subject);
                writer.WriteString("predicate", item.Fact.Predicate);
                writer.WritePropertyName("object");
                WriteFactObject(writer, item.Fact.Object);
                writer.WriteStartObject("origin");
                writer.WriteString("originId", item.Origin.OriginId);
                writer.WriteString("actor", item.Origin.Actor);
                writer.WriteString("commandId", item.Origin.CommandId);
                writer.WriteString(
                    "timestampUtc",
                    item.Origin.TimestampUtc.ToUniversalTime().ToString(
                        "O",
                        CultureInfo.InvariantCulture));
                writer.WriteEndObject();
                writer.WriteEndObject();
            }
            writer.WriteEndArray();
            writer.WriteStartArray("delete");
            foreach (var factId in record.Delete)
            {
                writer.WriteStringValue(factId);
            }
            writer.WriteEndArray();
            writer.WriteEndObject();
        }
        return stream.ToArray();
    }

    public static RuntimeLogRecord Deserialize(ReadOnlySpan<byte> payload)
    {
        try
        {
            using var document = JsonDocument.Parse(payload);
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                throw new RuntimeStateCorruptionException(
                    "Runtime log payload must be a JSON object.");
            }
            if (RequiredInt32(root, "formatVersion") != 1)
            {
                throw new RuntimeStateCorruptionException(
                    "Unsupported runtime log payload version.");
            }

            var snapshotId = RequiredString(root, "snapshotId");
            var commandId = RequiredString(root, "commandId");
            var requestHash = RequiredString(root, "requestHash");
            if (!requestHash.StartsWith("sha256:", StringComparison.Ordinal))
            {
                throw new RuntimeStateCorruptionException(
                    "Runtime command request hash is invalid.");
            }
            var actor = RequiredString(root, "actor");
            var acceptedAtUtc = RequiredTimestamp(root, "acceptedAtUtc");
            var beforeRevision = RequiredInt64(root, "beforeRevision");
            var afterRevision = RequiredInt64(root, "afterRevision");
            if (beforeRevision < 0 || afterRevision < 0)
            {
                throw new RuntimeStateCorruptionException(
                    "Runtime revisions cannot be negative.");
            }

            var add = ReadAdd(
                RequiredArray(root, "add"),
                commandId,
                actor,
                acceptedAtUtc);
            var delete = RequiredArray(root, "delete")
                .EnumerateArray()
                .Select(static item => item.ValueKind == JsonValueKind.String
                    ? item.GetString()
                        ?? throw new RuntimeStateCorruptionException(
                            "Delete FactId is null.")
                    : throw new RuntimeStateCorruptionException(
                        "Delete FactId must be a string."))
                .ToArray();
            RequireSortedUnique(
                add.Select(static item => item.Fact.FactId),
                "added FactIds");
            RequireSortedUnique(delete, "deleted FactIds");

            var changed = add.Length > 0 || delete.Length > 0;
            var expectedAfter = changed
                ? checked(beforeRevision + 1)
                : beforeRevision;
            if (afterRevision != expectedAfter)
            {
                throw new RuntimeStateCorruptionException(
                    "Runtime log revision transition is invalid.");
            }

            return new RuntimeLogRecord(
                snapshotId,
                commandId,
                requestHash,
                actor,
                acceptedAtUtc,
                beforeRevision,
                afterRevision,
                add,
                delete);
        }
        catch (RuntimeStateCorruptionException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is JsonException
            or InvalidOperationException
            or FormatException
            or OverflowException)
        {
            throw new RuntimeStateCorruptionException(
                "Runtime log payload is invalid.",
                exception);
        }
    }

    private static LoggedAdd[] ReadAdd(
        JsonElement array,
        string commandId,
        string actor,
        DateTimeOffset acceptedAtUtc)
    {
        var add = new List<LoggedAdd>();
        foreach (var item in array.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object)
            {
                throw new RuntimeStateCorruptionException(
                    "Added fact must be an object.");
            }
            var factId = RequiredString(item, "factId");
            var subject = RequiredString(item, "subject");
            var predicate = RequiredString(item, "predicate");
            var fact = CanonicalFact.Create(
                subject,
                predicate,
                ReadFactObject(RequiredObject(item, "object")));
            if (!StringComparer.Ordinal.Equals(fact.FactId, factId))
            {
                throw new RuntimeStateCorruptionException(
                    $"Added fact '{factId}' does not match its canonical content.");
            }

            var originJson = RequiredObject(item, "origin");
            var originId = RequiredString(originJson, "originId");
            var originActor = RequiredString(originJson, "actor");
            var originCommandId = RequiredString(originJson, "commandId");
            var originTimestamp = RequiredTimestamp(originJson, "timestampUtc");
            if (!StringComparer.Ordinal.Equals(originActor, actor)
                || !StringComparer.Ordinal.Equals(originCommandId, commandId)
                || originTimestamp != acceptedAtUtc
                || !StringComparer.Ordinal.Equals(
                    originId,
                    RuntimeLogRecord.EditOriginId(commandId, factId)))
            {
                throw new RuntimeStateCorruptionException(
                    $"Edit origin for added fact '{factId}' is inconsistent.");
            }
            add.Add(new LoggedAdd(
                fact,
                new EditRuntimeFactOrigin(
                    originId,
                    originActor,
                    originCommandId,
                    originTimestamp)));
        }
        return add.ToArray();
    }

    private static void WriteFactObject(Utf8JsonWriter writer, FactObject value)
    {
        writer.WriteStartObject();
        switch (value)
        {
            case IriObject iri:
                writer.WriteString("kind", "iri");
                writer.WriteString("value", iri.Value);
                break;
            case LiteralObject literal:
                writer.WriteString("kind", "literal");
                writer.WriteString("lexical", literal.Lexical);
                writer.WriteString(
                    "literalKind",
                    literal.Kind switch
                    {
                        LiteralKind.Plain => "plain",
                        LiteralKind.Language => "language",
                        LiteralKind.Datatype => "datatype",
                        _ => throw new ArgumentOutOfRangeException(
                            nameof(value),
                            value,
                            "Unsupported literal kind.")
                    });
                if (literal.Kind == LiteralKind.Language)
                {
                    writer.WriteString(
                        "language",
                        literal.Language
                        ?? throw new InvalidOperationException(
                            "Language literal has no language tag."));
                }
                else if (literal.Kind == LiteralKind.Datatype)
                {
                    writer.WriteString(
                        "datatype",
                        literal.Datatype
                        ?? throw new InvalidOperationException(
                            "Datatype literal has no datatype IRI."));
                }
                break;
            default:
                throw new ArgumentOutOfRangeException(
                    nameof(value),
                    value,
                    "Unsupported fact object.");
        }
        writer.WriteEndObject();
    }

    private static FactObject ReadFactObject(JsonElement value)
    {
        var kind = RequiredString(value, "kind");
        return kind switch
        {
            "iri" => new IriObject(RequiredString(value, "value")),
            "literal" => ReadLiteral(value),
            _ => throw new RuntimeStateCorruptionException(
                $"Unsupported fact object kind '{kind}'.")
        };
    }

    private static FactObject ReadLiteral(JsonElement value)
    {
        var lexical = RequiredStringAllowEmpty(value, "lexical");
        return RequiredString(value, "literalKind") switch
        {
            "plain" => LiteralObject.Plain(lexical),
            "language" => LiteralObject.LanguageTagged(
                lexical,
                RequiredString(value, "language")),
            "datatype" => LiteralObject.DatatypeTagged(
                lexical,
                RequiredString(value, "datatype")),
            var literalKind => throw new RuntimeStateCorruptionException(
                $"Unsupported literal kind '{literalKind}'.")
        };
    }

    private static void RequireSortedUnique(
        IEnumerable<string> values,
        string description)
    {
        string? previous = null;
        foreach (var value in values)
        {
            if (previous is not null
                && StringComparer.Ordinal.Compare(previous, value) >= 0)
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log {description} must be sorted and unique.");
            }
            previous = value;
        }
    }

    private static JsonElement RequiredObject(JsonElement parent, string name)
    {
        if (!parent.TryGetProperty(name, out var value)
            || value.ValueKind != JsonValueKind.Object)
        {
            throw new RuntimeStateCorruptionException(
                $"Required object '{name}' is missing.");
        }
        return value;
    }

    private static JsonElement RequiredArray(JsonElement parent, string name)
    {
        if (!parent.TryGetProperty(name, out var value)
            || value.ValueKind != JsonValueKind.Array)
        {
            throw new RuntimeStateCorruptionException(
                $"Required array '{name}' is missing.");
        }
        return value;
    }

    private static string RequiredString(JsonElement parent, string name)
    {
        var value = RequiredStringAllowEmpty(parent, name);
        if (value.Length == 0)
        {
            throw new RuntimeStateCorruptionException(
                $"Required string '{name}' is empty.");
        }
        return value;
    }

    private static string RequiredStringAllowEmpty(JsonElement parent, string name)
    {
        if (!parent.TryGetProperty(name, out var value)
            || value.ValueKind != JsonValueKind.String)
        {
            throw new RuntimeStateCorruptionException(
                $"Required string '{name}' is missing.");
        }
        return value.GetString()
            ?? throw new RuntimeStateCorruptionException(
                $"Required string '{name}' is null.");
    }

    private static int RequiredInt32(JsonElement parent, string name)
    {
        if (!parent.TryGetProperty(name, out var value)
            || !value.TryGetInt32(out var result))
        {
            throw new RuntimeStateCorruptionException(
                $"Required integer '{name}' is missing.");
        }
        return result;
    }

    private static long RequiredInt64(JsonElement parent, string name)
    {
        if (!parent.TryGetProperty(name, out var value)
            || !value.TryGetInt64(out var result))
        {
            throw new RuntimeStateCorruptionException(
                $"Required integer '{name}' is missing.");
        }
        return result;
    }

    private static DateTimeOffset RequiredTimestamp(JsonElement parent, string name)
    {
        var text = RequiredString(parent, name);
        if (!DateTimeOffset.TryParseExact(
                text,
                "O",
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var value))
        {
            throw new RuntimeStateCorruptionException(
                $"Timestamp '{name}' is invalid.");
        }
        return value.ToUniversalTime();
    }
}
