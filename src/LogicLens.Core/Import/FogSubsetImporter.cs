using System.Xml;
using System.Xml.Linq;
using LogicLens.Core.Model;

namespace LogicLens.Core.Import;

public sealed record FogOriginContext(
    string SourcePath,
    string SourceDbId,
    string EntityId);

public sealed record ImportedFactOccurrence(
    CanonicalFact Fact,
    Origin Origin);

public sealed record FogImportResult(
    string SourcePath,
    string SourceDbId,
    IReadOnlyList<ImportedFactOccurrence> Occurrences);

public sealed class FogSubsetImporter
{
    public const string RdfNamespace =
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#";

    public const string RdfType = RdfNamespace + "type";

    private static readonly XNamespace Rdf = RdfNamespace;
    private static readonly XNamespace Xml = XNamespace.Xml;

    public FogImportResult Import(
        Stream xml,
        string sourcePath,
        Func<FogOriginContext, Origin> originFactory)
    {
        ArgumentNullException.ThrowIfNull(xml);
        if (string.IsNullOrWhiteSpace(sourcePath))
        {
            throw new ArgumentException(
                "Source path cannot be null, empty, or whitespace.",
                nameof(sourcePath));
        }

        ArgumentNullException.ThrowIfNull(originFactory);

        XDocument document;
        try
        {
            document = XDocument.Load(
                xml,
                LoadOptions.PreserveWhitespace | LoadOptions.SetLineInfo);
        }
        catch (XmlException exception)
        {
            throw new FogImportException(
                sourcePath,
                "FOG input is not valid XML.",
                exception);
        }

        var root = document.Root
            ?? throw new FogImportException(sourcePath, "FOG document has no root element.");

        if (root.Name != Rdf + "RDF")
        {
            throw new FogImportException(
                sourcePath,
                $"Expected rdf:RDF root, got '{root.Name}'.");
        }

        var sourceDbId = RequiredAttribute(root, "dbid", sourcePath);
        var occurrences = new List<ImportedFactOccurrence>();

        foreach (var entity in root.Elements())
        {
            var subject = RequiredAttribute(entity, Rdf + "about", sourcePath);
            var context = new FogOriginContext(sourcePath, sourceDbId, subject);
            var origin = originFactory(context)
                ?? throw new FogImportException(
                    sourcePath,
                    $"Origin factory returned null for '{subject}'.");

            if (!StringComparer.Ordinal.Equals(origin.SourcePath, sourcePath)
                || !StringComparer.Ordinal.Equals(origin.SourceDbId, sourceDbId)
                || !StringComparer.Ordinal.Equals(origin.EntityId, subject))
            {
                throw new FogImportException(
                    sourcePath,
                    $"Origin '{origin.OriginId}' does not match source entity '{subject}'.");
            }

            var typeIri = ExpandedName(entity.Name);
            occurrences.Add(new ImportedFactOccurrence(
                CanonicalFact.Create(subject, RdfType, new IriObject(typeIri)),
                origin));

            foreach (var property in entity.Elements())
            {
                occurrences.Add(new ImportedFactOccurrence(
                    ParseProperty(subject, property, sourcePath),
                    origin));
            }
        }

        return new FogImportResult(sourcePath, sourceDbId, occurrences);
    }

    private static CanonicalFact ParseProperty(
        string subject,
        XElement property,
        string sourcePath)
    {
        if (property.HasElements)
        {
            throw At(
                sourcePath,
                property,
                "Nested property elements are outside the supported FOG subset.");
        }

        var predicate = ExpandedName(property.Name);
        var resource = property.Attribute(Rdf + "resource")?.Value;
        var language = property.Attribute(Xml + "lang")?.Value;
        var datatype = property.Attribute(Rdf + "datatype")?.Value;

        if (language is not null && datatype is not null)
        {
            throw At(
                sourcePath,
                property,
                "A literal cannot have both xml:lang and rdf:datatype.");
        }

        FactObject value;
        if (resource is not null)
        {
            if (language is not null
                || datatype is not null
                || property.Nodes().OfType<XText>().Any(
                    static text => !string.IsNullOrWhiteSpace(text.Value)))
            {
                throw At(
                    sourcePath,
                    property,
                    "rdf:resource property cannot also contain literal content.");
            }

            value = new IriObject(resource);
        }
        else if (language is not null)
        {
            value = LiteralObject.LanguageTagged(property.Value, language);
        }
        else if (datatype is not null)
        {
            value = LiteralObject.DatatypeTagged(property.Value, datatype);
        }
        else
        {
            value = LiteralObject.Plain(property.Value);
        }

        return CanonicalFact.Create(subject, predicate, value);
    }

    private static string ExpandedName(XName name)
    {
        if (string.IsNullOrEmpty(name.NamespaceName))
        {
            throw new InvalidOperationException(
                $"FOG entity and property names must be namespace-qualified: '{name.LocalName}'.");
        }

        return name.NamespaceName + name.LocalName;
    }

    private static string RequiredAttribute(
        XElement element,
        XName attributeName,
        string sourcePath)
    {
        var value = element.Attribute(attributeName)?.Value;
        if (string.IsNullOrWhiteSpace(value))
        {
            throw At(
                sourcePath,
                element,
                $"Required attribute '{attributeName}' is missing or empty.");
        }

        return value;
    }

    private static FogImportException At(
        string sourcePath,
        XObject node,
        string message)
    {
        var lineInfo = (IXmlLineInfo)node;
        var suffix = lineInfo.HasLineInfo()
            ? $" Line {lineInfo.LineNumber}, position {lineInfo.LinePosition}."
            : string.Empty;

        return new FogImportException(sourcePath, message + suffix);
    }
}

public sealed class FogImportException : Exception
{
    public FogImportException(string sourcePath, string message)
        : base($"{sourcePath}: {message}")
    {
        SourcePath = sourcePath;
    }

    public FogImportException(
        string sourcePath,
        string message,
        Exception innerException)
        : base($"{sourcePath}: {message}", innerException)
    {
        SourcePath = sourcePath;
    }

    public string SourcePath { get; }
}
