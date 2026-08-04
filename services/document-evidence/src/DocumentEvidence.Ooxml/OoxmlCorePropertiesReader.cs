using System.Globalization;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

internal static class OoxmlCorePropertiesReader
{
    private static readonly Regex Whitespace = new(
        "\\s+",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly XNamespace Dc = "http://purl.org/dc/elements/1.1/";
    private static readonly XNamespace Dcterms = "http://purl.org/dc/terms/";

    public static OoxmlCoreProperties Read(OoxmlPart? part)
    {
        if (part is null)
        {
            return new OoxmlCoreProperties(null, null, null, null, null, null);
        }
        var document = OoxmlXml.Parse(part, 1_048_576);
        var root = document.Root
            ?? throw new InvalidDataException("OOXML core properties root is missing.");
        return new OoxmlCoreProperties(
            Text(root.Element(Dc + "title")),
            Text(root.Element(Dc + "subject")),
            Text(root.Element(Dc + "creator")),
            Text(root.Element(Dc + "description")),
            Timestamp(root.Element(Dcterms + "created")),
            Timestamp(root.Element(Dcterms + "modified"))
        );
    }

    private static string? Text(XElement? element)
    {
        if (element is null)
        {
            return null;
        }
        var value = Whitespace.Replace(element.Value, " ").Trim();
        return value.Length == 0 ? null : value;
    }

    private static string? Timestamp(XElement? element)
    {
        var value = Text(element);
        if (value is null)
        {
            return null;
        }
        if (!DateTimeOffset.TryParse(
            value,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AllowWhiteSpaces | DateTimeStyles.AssumeUniversal,
            out var parsed
        ))
        {
            throw new InvalidDataException($"Invalid OOXML core timestamp: {value}");
        }
        return parsed.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture);
    }
}
