using System.Xml.Linq;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

internal static class XlsxSharedStrings
{
    private static readonly XNamespace Spreadsheet =
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main";

    public static IReadOnlyList<string> Read(OoxmlPart? part)
    {
        if (part is null)
        {
            return [];
        }
        var document = OoxmlXml.Parse(part);
        return document.Root?
            .Elements(Spreadsheet + "si")
            .Select(item => string.Concat(item.Descendants(Spreadsheet + "t").Select(text => text.Value)))
            .ToArray()
            ?? [];
    }

    public static string Demand(IReadOnlyList<string> values, string rawIndex)
    {
        if (!int.TryParse(rawIndex, out var index) || index < 0 || index >= values.Count)
        {
            throw new InvalidDataException($"Invalid XLSX shared-string index: {rawIndex}");
        }
        return values[index];
    }
}
