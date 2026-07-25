using System.Text;
using System.Text.Json.Nodes;

namespace LogicLens.Ui.Validation;

public sealed class UiDocumentSemanticValidator
{
    private readonly UiDocumentValidationOptions options;

    public UiDocumentSemanticValidator(UiDocumentValidationOptions? options = null)
    {
        this.options = options ?? new UiDocumentValidationOptions();
    }

    public IReadOnlyList<UiDocumentValidationError> Validate(
        JsonObject document,
        JsonArray authoritativeFacts,
        string rootEntityId)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(authoritativeFacts);
        ArgumentException.ThrowIfNullOrWhiteSpace(rootEntityId);

        var state = new State(
            options,
            AuthoritativeFactIndex.Build(authoritativeFacts),
            rootEntityId);
        state.CheckDocumentSize(document);
        state.VisitDocument(document);
        state.CheckOccurrences();
        state.CheckFactCoverage();
        return state.Errors;
    }

    private sealed class State
    {
        private readonly UiDocumentValidationOptions options;
        private readonly AuthoritativeFactIndex facts;
        private readonly string rootEntityId;
        private readonly HashSet<string> componentIds = new(StringComparer.Ordinal);
        private readonly Dictionary<string, Occurrence> occurrences =
            new(StringComparer.Ordinal);
        private readonly Dictionary<string, List<bool>> displayedFacts =
            new(StringComparer.Ordinal);
        private readonly List<UiDocumentValidationError> errors = [];
        private int componentCount;
        private int valueCount;

        public State(
            UiDocumentValidationOptions options,
            AuthoritativeFactIndex facts,
            string rootEntityId)
        {
            this.options = options;
            this.facts = facts;
            this.rootEntityId = rootEntityId;
        }

        public IReadOnlyList<UiDocumentValidationError> Errors => errors
            .OrderBy(static error => error.Path, StringComparer.Ordinal)
            .ThenBy(static error => error.Code, StringComparer.Ordinal)
            .ThenBy(static error => error.Message, StringComparer.Ordinal)
            .Take(options.MaxErrors)
            .ToArray();

        public void CheckDocumentSize(JsonObject document)
        {
            var bytes = Encoding.UTF8.GetByteCount(document.ToJsonString());
            if (bytes > options.MaxDocumentBytes)
            {
                Add(
                    "document_bytes",
                    "",
                    $"Document size {bytes} exceeds {options.MaxDocumentBytes} bytes.");
            }
        }

        public void VisitDocument(JsonObject document)
        {
            var context = Object(document, "context");
            var contextEntity = String(context, "entityId");
            if (!StringComparer.Ordinal.Equals(contextEntity, rootEntityId))
            {
                Add(
                    "context_entity",
                    "/context/entityId",
                    "Document context does not match the requested entity.");
            }

            var page = Object(document, "page");
            AddComponentId(String(page, "id"), "/page/id");
            CheckPlainText(String(page, "title"), "/page/title");

            var sections = Array(page, "sections");
            for (var index = 0; index < sections.Count; index++)
            {
                VisitSection(
                    Object(sections, index),
                    $"/page/sections/{index}",
                    1,
                    rootEntityId,
                    null,
                    false);
            }

            var diagnostics = Array(document, "diagnostics");
            for (var index = 0; index < diagnostics.Count; index++)
            {
                VisitDiagnostic(
                    Object(diagnostics, index),
                    $"/diagnostics/{index}");
            }
        }

        public void CheckOccurrences()
        {
            foreach (var occurrence in occurrences.Values.OrderBy(
                         static item => item.Id,
                         StringComparer.Ordinal))
            {
                if (!facts.Nodes.Contains(occurrence.NodeId)
                    && !StringComparer.Ordinal.Equals(
                        occurrence.NodeId,
                        rootEntityId))
                {
                    Add(
                        "occurrence_node",
                        occurrence.Path + "/nodeId",
                        "Occurrence node does not exist in the active fact slice.");
                }

                if (occurrence.ParentId is null)
                {
                    if (occurrence.Depth != 0
                        || occurrence.ViaFactId is not null
                        || !StringComparer.Ordinal.Equals(
                            occurrence.Direction,
                            "root"))
                    {
                        Add(
                            "occurrence_root",
                            occurrence.Path,
                            "Root occurrence has inconsistent depth, direction, or via fact.");
                    }

                    continue;
                }

                if (!occurrences.TryGetValue(occurrence.ParentId, out var parent))
                {
                    Add(
                        "occurrence_parent",
                        occurrence.Path + "/parentOccurrenceId",
                        "Occurrence parent does not exist.");
                    continue;
                }

                if (occurrence.Depth != parent.Depth + 1)
                {
                    Add(
                        "occurrence_depth",
                        occurrence.Path + "/depth",
                        "Occurrence depth is not parent depth plus one.");
                }

                if (occurrence.ViaFactId is null
                    || !facts.TryGet(occurrence.ViaFactId, out var fact))
                {
                    Add(
                        "occurrence_fact",
                        occurrence.Path + "/viaFactId",
                        "Occurrence traversal fact does not exist.");
                    continue;
                }

                var connected = occurrence.Direction switch
                {
                    "outgoing" =>
                        StringComparer.Ordinal.Equals(parent.NodeId, fact.Subject)
                        && IsIri(fact.Object, occurrence.NodeId),
                    "incoming" =>
                        IsIri(fact.Object, parent.NodeId)
                        && StringComparer.Ordinal.Equals(occurrence.NodeId, fact.Subject),
                    _ => false
                };
                if (!connected)
                {
                    Add(
                        "occurrence_direction",
                        occurrence.Path + "/direction",
                        "Occurrence direction does not match its canonical traversal fact.");
                }
            }
        }

        public void CheckFactCoverage()
        {
            foreach (var factId in facts.FactIds.OrderBy(
                         static item => item,
                         StringComparer.Ordinal))
            {
                if (!displayedFacts.ContainsKey(factId))
                {
                    Add(
                        "fact_missing",
                        "/page",
                        $"Active base fact '{factId}' is not represented.");
                }
            }

            foreach (var pair in displayedFacts)
            {
                if (pair.Value.Count > 1 && pair.Value.Any(static nested => !nested))
                {
                    Add(
                        "fact_duplicate",
                        "/page",
                        $"Base fact '{pair.Key}' is repeated outside occurrence context.");
                }
            }
        }

        private void VisitSection(
            JsonObject section,
            string path,
            int sectionDepth,
            string inheritedNodeId,
            string? inheritedOccurrenceId,
            bool inheritedOccurrenceContext)
        {
            CountComponent(path);
            AddComponentId(String(section, "id"), path + "/id");
            CheckPlainText(String(section, "title"), path + "/title");
            if (sectionDepth > options.MaxSectionDepth)
            {
                Add(
                    "section_depth",
                    path,
                    $"Section nesting exceeds {options.MaxSectionDepth}.");
            }

            var nodeId = inheritedNodeId;
            var occurrenceId = inheritedOccurrenceId;
            var occurrenceContext = inheritedOccurrenceContext;
            if (section["occurrence"] is JsonObject occurrence)
            {
                occurrenceId = String(occurrence, "occurrenceId");
                nodeId = String(occurrence, "nodeId");
                occurrenceContext = true;
                var value = new Occurrence(
                    occurrenceId,
                    nodeId,
                    Int(occurrence, "depth"),
                    NullableString(occurrence, "parentOccurrenceId"),
                    NullableString(occurrence, "viaFactId"),
                    String(occurrence, "direction"),
                    path + "/occurrence");
                if (!occurrences.TryAdd(occurrenceId, value))
                {
                    Add(
                        "occurrence_duplicate",
                        path + "/occurrence/occurrenceId",
                        "OccurrenceId must be unique in a document.");
                }

                if (inheritedOccurrenceId is not null
                    && !StringComparer.Ordinal.Equals(
                        value.ParentId,
                        inheritedOccurrenceId))
                {
                    Add(
                        "occurrence_nesting",
                        path + "/occurrence/parentOccurrenceId",
                        "Nested occurrence does not reference its containing occurrence.");
                }
            }

            var components = Array(section, "components");
            for (var index = 0; index < components.Count; index++)
            {
                var component = Object(components, index);
                var componentPath = path + "/components/" + index;
                switch (String(component, "kind"))
                {
                    case "section":
                        VisitSection(
                            component,
                            componentPath,
                            sectionDepth + 1,
                            nodeId,
                            occurrenceId,
                            occurrenceContext);
                        break;
                    case "property":
                        VisitProperty(
                            component,
                            componentPath,
                            nodeId,
                            occurrenceContext);
                        break;
                    case "textBlock":
                        VisitTextBlock(component, componentPath);
                        break;
                    case "rawProlog":
                        VisitRawProlog(component, componentPath);
                        break;
                    case "diagnostic":
                        VisitDiagnostic(component, componentPath);
                        break;
                }
            }
        }

        private void VisitProperty(
            JsonObject property,
            string path,
            string currentNodeId,
            bool occurrenceContext)
        {
            CountComponent(path);
            AddComponentId(String(property, "id"), path + "/id");
            CheckPlainText(String(property, "label"), path + "/label");
            var predicate = String(property, "predicate");
            var direction = String(property, "direction");
            var values = Array(property, "values");
            valueCount += values.Count;
            if (valueCount > options.MaxValues)
            {
                Add(
                    "value_count",
                    path + "/values",
                    $"Document values exceed {options.MaxValues}.");
            }

            for (var index = 0; index < values.Count; index++)
            {
                VisitValue(
                    Object(values, index),
                    path + "/values/" + index,
                    predicate,
                    direction,
                    currentNodeId,
                    occurrenceContext);
            }
        }

        private void VisitValue(
            JsonObject value,
            string path,
            string predicate,
            string direction,
            string currentNodeId,
            bool occurrenceContext)
        {
            var kind = String(value, "kind");
            if (kind == "resourceLink")
            {
                CheckResourceTarget(String(value, "targetId"), path + "/targetId");
                CheckPlainText(StringAllowEmpty(value, "label"), path + "/label");
            }

            var source = Object(value, "source");
            switch (String(source, "kind"))
            {
                case "base":
                    ValidateBaseSource(
                        source,
                        value,
                        path,
                        predicate,
                        direction,
                        currentNodeId,
                        occurrenceContext);
                    break;
                case "derived":
                    ValidateDerivedSource(source, value, path, direction);
                    break;
            }
        }

        private void ValidateBaseSource(
            JsonObject source,
            JsonObject value,
            string path,
            string predicate,
            string direction,
            string currentNodeId,
            bool occurrenceContext)
        {
            var snapshot = Object(source, "fact");
            var factId = String(snapshot, "factId");
            if (!facts.TryGet(factId, out var fact))
            {
                Add(
                    "fact_unknown",
                    path + "/source/fact/factId",
                    "Base source FactId does not exist at the declared revision.");
                return;
            }

            var exact = StringComparer.Ordinal.Equals(
                    String(snapshot, "subject"),
                    fact.Subject)
                && StringComparer.Ordinal.Equals(
                    String(snapshot, "predicate"),
                    fact.Predicate)
                && AuthoritativeFactIndex.JsonEqual(
                    snapshot["object"],
                    fact.Object);
            if (!exact)
            {
                Add(
                    "fact_snapshot",
                    path + "/source/fact",
                    "Embedded canonical fact does not match the active fact.");
            }

            var origins = Array(source, "origins")
                .Select(static item => item?.GetValue<string>() ?? string.Empty)
                .OrderBy(static item => item, StringComparer.Ordinal)
                .ToArray();
            if (!origins.SequenceEqual(fact.Origins, StringComparer.Ordinal))
            {
                Add(
                    "fact_origins",
                    path + "/source/origins",
                    "Base source origins do not match the active fact origins.");
            }

            if (!StringComparer.Ordinal.Equals(predicate, fact.Predicate))
            {
                Add(
                    "property_predicate",
                    path,
                    "Property predicate does not match its source fact.");
            }

            var directionValid = direction switch
            {
                "outgoing" =>
                    StringComparer.Ordinal.Equals(currentNodeId, fact.Subject)
                    && ValueMatchesOutgoing(value, fact.Object),
                "incoming" =>
                    IsIri(fact.Object, currentNodeId)
                    && ValueMatchesIncoming(value, fact.Subject),
                _ => false
            };
            if (!directionValid)
            {
                Add(
                    "property_direction",
                    path,
                    "Displayed value and direction do not match the canonical fact.");
            }

            if (!displayedFacts.TryGetValue(factId, out var contexts))
            {
                contexts = [];
                displayedFacts.Add(factId, contexts);
            }
            contexts.Add(occurrenceContext);
        }

        private void ValidateDerivedSource(
            JsonObject source,
            JsonObject value,
            string path,
            string direction)
        {
            if (!StringComparer.Ordinal.Equals(direction, "derived"))
            {
                Add(
                    "derived_direction",
                    path,
                    "Derived source requires property direction 'derived'.");
            }

            if (Bool(value, "editable"))
            {
                Add(
                    "derived_editable",
                    path + "/editable",
                    "Derived values must be read-only.");
            }

            var evidence = Array(source, "evidenceFactIds");
            for (var index = 0; index < evidence.Count; index++)
            {
                var factId = evidence[index]?.GetValue<string>() ?? string.Empty;
                if (!facts.TryGet(factId, out _))
                {
                    Add(
                        "evidence_fact",
                        path + "/source/evidenceFactIds/" + index,
                        "Derived evidence FactId does not exist.");
                }
            }
        }

        private void VisitTextBlock(JsonObject value, string path)
        {
            CountComponent(path);
            AddComponentId(String(value, "id"), path + "/id");
            CheckPlainText(StringAllowEmpty(value, "text"), path + "/text");
            if (value["source"] is JsonObject source
                && StringComparer.Ordinal.Equals(String(source, "kind"), "base"))
            {
                Add(
                    "text_block_base",
                    path + "/source",
                    "A data-derived TextBlock must use a derived source.");
            }
        }

        private void VisitRawProlog(JsonObject value, string path)
        {
            CountComponent(path);
            AddComponentId(String(value, "id"), path + "/id");
            CheckPlainText(String(value, "title"), path + "/title");
        }

        private void VisitDiagnostic(JsonObject value, string path)
        {
            CountComponent(path);
            AddComponentId(String(value, "id"), path + "/id");
            CheckPlainText(String(value, "message"), path + "/message");
        }

        private void CountComponent(string path)
        {
            componentCount++;
            if (componentCount > options.MaxComponents)
            {
                Add(
                    "component_count",
                    path,
                    $"Document components exceed {options.MaxComponents}.");
            }
        }

        private void AddComponentId(string id, string path)
        {
            if (!componentIds.Add(id))
            {
                Add("component_id", path, "Component ID must be unique.");
            }
        }

        private void CheckPlainText(string value, string path)
        {
            if (ContainsActiveMarkup(value))
            {
                Add(
                    "active_markup",
                    path,
                    "Trusted UI text cannot contain active HTML or script markup.");
            }
        }

        private void CheckResourceTarget(string targetId, string path)
        {
            var forbidden = new[] { "javascript:", "data:", "vbscript:", "file:" };
            if (forbidden.Any(prefix => targetId.StartsWith(
                    prefix,
                    StringComparison.OrdinalIgnoreCase)))
            {
                Add(
                    "resource_scheme",
                    path,
                    "Resource link uses a forbidden executable or local scheme.");
            }
        }

        private void Add(string code, string path, string message)
        {
            if (errors.Count < options.MaxErrors)
            {
                errors.Add(new UiDocumentValidationError(code, path, message));
            }
        }

        private static bool ValueMatchesOutgoing(
            JsonObject value,
            JsonObject factObject)
        {
            var valueKind = String(value, "kind");
            var objectKind = String(factObject, "kind");
            return (valueKind, objectKind) switch
            {
                ("resourceLink", "iri") => StringComparer.Ordinal.Equals(
                    String(value, "targetId"),
                    String(factObject, "resourceId")),
                ("text", "literal") =>
                    StringComparer.Ordinal.Equals(
                        StringAllowEmpty(value, "text"),
                        StringAllowEmpty(factObject, "lexical"))
                    && StringComparer.Ordinal.Equals(
                        String(value, "literalKind"),
                        String(factObject, "literalKind"))
                    && NullableNodeEqual(value["language"], factObject["language"])
                    && NullableNodeEqual(value["datatype"], factObject["datatype"]),
                _ => false
            };
        }

        private static bool ValueMatchesIncoming(JsonObject value, string subject) =>
            StringComparer.Ordinal.Equals(String(value, "kind"), "resourceLink")
            && StringComparer.Ordinal.Equals(String(value, "targetId"), subject);

        private static bool IsIri(JsonObject value, string resourceId) =>
            StringComparer.Ordinal.Equals(String(value, "kind"), "iri")
            && StringComparer.Ordinal.Equals(
                String(value, "resourceId"),
                resourceId);

        private static bool NullableNodeEqual(JsonNode? first, JsonNode? second) =>
            JsonNode.DeepEquals(first, second);

        private static bool ContainsActiveMarkup(string value)
        {
            var patterns = new[]
            {
                "<script", "</script", "<iframe", "<object", "<embed",
                "<svg", "onerror=", "onload="
            };
            return patterns.Any(pattern => value.Contains(
                pattern,
                StringComparison.OrdinalIgnoreCase));
        }

        private static JsonObject Object(JsonObject parent, string name) =>
            parent[name]!.AsObject();

        private static JsonObject Object(JsonArray parent, int index) =>
            parent[index]!.AsObject();

        private static JsonArray Array(JsonObject parent, string name) =>
            parent[name]!.AsArray();

        private static string String(JsonObject parent, string name) =>
            parent[name]!.GetValue<string>();

        private static string StringAllowEmpty(JsonObject parent, string name) =>
            parent[name]!.GetValue<string>();

        private static string? NullableString(JsonObject parent, string name) =>
            parent[name] is null ? null : parent[name]!.GetValue<string>();

        private static int Int(JsonObject parent, string name) =>
            parent[name]!.GetValue<int>();

        private static bool Bool(JsonObject parent, string name) =>
            parent[name]!.GetValue<bool>();
    }

    private sealed record Occurrence(
        string Id,
        string NodeId,
        int Depth,
        string? ParentId,
        string? ViaFactId,
        string Direction,
        string Path);
}
