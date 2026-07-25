using System.Xml;
using System.Xml.Linq;

namespace LogicLens.OntologyCompiler;

internal sealed class OntologySubsetImporter
{
    private const string RdfNamespace =
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#";

    private static readonly XNamespace Rdf = RdfNamespace;
    private static readonly XNamespace Xml = XNamespace.Xml;

    private static readonly IReadOnlyDictionary<string, OntologyTermKind> TermKinds =
        new Dictionary<string, OntologyTermKind>(StringComparer.Ordinal)
        {
            ["Class"] = OntologyTermKind.Class,
            ["DatatypeProperty"] = OntologyTermKind.DatatypeProperty,
            ["ObjectProperty"] = OntologyTermKind.ObjectProperty,
            ["EnumerationType"] = OntologyTermKind.EnumerationType
        };

    private static readonly HashSet<string> IgnoredChildElements =
        new(StringComparer.Ordinal)
        {
            "domain",
            "range",
            "SubClassOf",
            "state"
        };

    private static readonly HashSet<XName> AllowedRootAttributes =
    [
        XName.Get("dbid")
    ];

    private static readonly HashSet<XName> AllowedTermAttributes =
    [
        Rdf + "about",
        XName.Get("priority"),
        XName.Get("abstract"),
        XName.Get("essential"),
        XName.Get("weight")
    ];

    private static readonly HashSet<XName> AllowedLabelAttributes =
    [
        Xml + "lang"
    ];

    public OntologySnapshot Import(Stream xml, string sourcePath)
    {
        ArgumentNullException.ThrowIfNull(xml);
        if (string.IsNullOrWhiteSpace(sourcePath))
        {
            throw new ArgumentException(
                "Source path cannot be null, empty, or whitespace.",
                nameof(sourcePath));
        }

        XDocument document;
        try
        {
            document = XDocument.Load(
                xml,
                LoadOptions.PreserveWhitespace | LoadOptions.SetLineInfo);
        }
        catch (XmlException exception)
        {
            throw new OntologyImportException(
                sourcePath,
                "Ontology input is not valid XML.",
                exception);
        }

        var root = document.Root
            ?? throw new OntologyImportException(
                sourcePath,
                "Ontology document has no root element.");

        if (!string.IsNullOrEmpty(root.Name.NamespaceName)
            || !StringComparer.Ordinal.Equals(root.Name.LocalName, "Ontology"))
        {
            throw At(
                sourcePath,
                root,
                $"Expected unqualified Ontology root, got '{root.Name}'.");
        }

        ValidateAttributes(root, AllowedRootAttributes, sourcePath);
        var sourceDbId = RequiredAttribute(root, "dbid", sourcePath);
        var terms = new Dictionary<string, OntologyTerm>(StringComparer.Ordinal);

        foreach (var element in root.Elements())
        {
            if (!string.IsNullOrEmpty(element.Name.NamespaceName)
                || !TermKinds.TryGetValue(element.Name.LocalName, out var kind))
            {
                throw At(
                    sourcePath,
                    element,
                    $"Unsupported ontology term element '{element.Name}'.");
            }

            ValidateAttributes(element, AllowedTermAttributes, sourcePath);
            var id = RequiredAttribute(element, Rdf + "about", sourcePath);
            var priority = OptionalNonEmptyAttribute(element, "priority", sourcePath);
            var labels = ParseLabels(element, sourcePath);
            var term = new OntologyTerm(id, kind, priority, labels);

            if (!terms.TryAdd(id, term))
            {
                throw At(
                    sourcePath,
                    element,
                    $"Duplicate ontology term '{id}'.");
            }
        }

        return new OntologySnapshot(
            sourcePath,
            sourceDbId,
            terms.Values
                .OrderBy(static term => term.Id, StringComparer.Ordinal)
                .ToArray());
    }

    private static IReadOnlyList<OntologyLabel> ParseLabels(
        XElement term,
        string sourcePath)
    {
        var labels = new HashSet<OntologyLabel>();

        foreach (var child in term.Elements())
        {
            if (!string.IsNullOrEmpty(child.Name.NamespaceName))
            {
                throw At(
                    sourcePath,
                    child,
                    $"Namespaced ontology child '{child.Name}' is unsupported.");
            }

            var direction = child.Name.LocalName switch
            {
                "label" => OntologyLabelDirection.Forward,
                "inverse-label" => OntologyLabelDirection.Inverse,
                _ when IgnoredChildElements.Contains(child.Name.LocalName) =>
                    (OntologyLabelDirection?)null,
                _ => throw At(
                    sourcePath,
                    child,
                    $"Unsupported ontology child element '{child.Name.LocalName}'.")
            };

            if (direction is null)
            {
                continue;
            }

            ValidateAttributes(child, AllowedLabelAttributes, sourcePath);
            if (child.HasElements)
            {
                throw At(
                    sourcePath,
                    child,
                    "Ontology label cannot contain nested elements.");
            }

            var language = child.Attribute(Xml + "lang")?.Value;
            language = string.IsNullOrWhiteSpace(language)
                ? "plain"
                : language.ToLowerInvariant();
            var text = child.Value;
            if (string.IsNullOrWhiteSpace(text))
            {
                throw At(sourcePath, child, "Ontology label cannot be empty.");
            }

            labels.Add(new OntologyLabel(direction.Value, language, text));
        }

        return labels
            .OrderBy(static label => label.Direction)
            .ThenBy(static label => label.Language, StringComparer.Ordinal)
            .ThenBy(static label => label.Text, StringComparer.Ordinal)
            .ToArray();
    }

    private static void ValidateAttributes(
        XElement element,
        IReadOnlySet<XName> allowed,
        string sourcePath)
    {
        foreach (var attribute in element.Attributes())
        {
            if (attribute.IsNamespaceDeclaration)
            {
                continue;
            }

            if (!allowed.Contains(attribute.Name))
            {
                throw At(
                    sourcePath,
                    attribute,
                    $"Attribute '{attribute.Name}' is outside the supported ontology subset.");
            }
        }
    }

    private static string RequiredAttribute(
        XElement element,
        XName name,
        string sourcePath)
    {
        var value = element.Attribute(name)?.Value;
        if (string.IsNullOrWhiteSpace(value))
        {
            throw At(
                sourcePath,
                element,
                $"Required attribute '{name}' is missing or empty.");
        }

        return value;
    }

    private static string? OptionalNonEmptyAttribute(
        XElement element,
        XName name,
        string sourcePath)
    {
        var attribute = element.Attribute(name);
        if (attribute is null)
        {
            return null;
        }

        if (string.IsNullOrWhiteSpace(attribute.Value))
        {
            throw At(sourcePath, attribute, $"Attribute '{name}' cannot be empty.");
        }

        return attribute.Value;
    }

    private static OntologyImportException At(
        string sourcePath,
        XObject node,
        string message)
    {
        var lineInfo = (IXmlLineInfo)node;
        var suffix = lineInfo.HasLineInfo()
            ? $" Line {lineInfo.LineNumber}, position {lineInfo.LinePosition}."
            : string.Empty;

        return new OntologyImportException(sourcePath, message + suffix);
    }
}

internal sealed class OntologyImportException : Exception
{
    public OntologyImportException(string sourcePath, string message)
        : base($"{sourcePath}: {message}")
    {
        SourcePath = sourcePath;
    }

    public OntologyImportException(
        string sourcePath,
        string message,
        Exception innerException)
        : base($"{sourcePath}: {message}", innerException)
    {
        SourcePath = sourcePath;
    }

    public string SourcePath { get; }
}
