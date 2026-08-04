using System.Globalization;
using System.Xml.Linq;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

internal static class XlsxWorksheetParser
{
    private static readonly XNamespace Spreadsheet =
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main";

    public static XlsxSheet Parse(
        OoxmlPart part,
        int sheetIndex,
        string sheetName,
        IReadOnlyList<string> sharedStrings
    )
    {
        var document = OoxmlXml.Parse(part);
        var cells = new List<XlsxCell>();
        var references = new HashSet<string>(StringComparer.Ordinal);
        foreach (var element in document.Descendants(Spreadsheet + "c"))
        {
            var reference = ((string?)element.Attribute("r"))?.Trim()
                ?? throw new InvalidDataException("XLSX cell reference is missing.");
            if (!references.Add(reference))
            {
                throw new InvalidDataException($"Duplicate XLSX cell reference: {reference}");
            }
            var (row, column) = XlsxCellReference.Parse(reference);
            var value = ReadValue(element, sharedStrings);
            if (value.Formula is null && value.Raw is null && value.Display is null)
            {
                continue;
            }
            var anchor = new XlsxCellAnchor(
                sheetIndex,
                sheetName,
                row,
                column,
                reference
            );
            var contentHash = OoxmlHashing.Sha256(string.Join(
                '\0',
                sheetIndex.ToString(CultureInfo.InvariantCulture),
                sheetName,
                reference,
                value.Kind,
                value.Formula ?? "",
                value.Raw ?? "",
                value.Display ?? ""
            ));
            cells.Add(new XlsxCell(
                $"xlsx:{OoxmlHashing.Sha256($"{sheetName}:{reference}")[..20]}",
                value.Kind,
                value.Formula,
                value.Raw,
                value.Formula is null ? null : value.Raw,
                value.Display,
                contentHash,
                anchor
            ));
        }
        return new XlsxSheet(
            sheetIndex,
            sheetName,
            part.Name,
            cells.OrderBy(item => item.Anchor.RowIndex)
                .ThenBy(item => item.Anchor.ColumnIndex)
                .ToArray()
        );
    }

    private static CellValue ReadValue(
        XElement cell,
        IReadOnlyList<string> sharedStrings
    )
    {
        var type = ((string?)cell.Attribute("t"))?.Trim() ?? "n";
        var formula = Normalize(cell.Element(Spreadsheet + "f")?.Value);
        var raw = Normalize(cell.Element(Spreadsheet + "v")?.Value);
        return type switch
        {
            "s" => new CellValue("shared-string", formula, raw, raw is null
                ? null
                : XlsxSharedStrings.Demand(sharedStrings, raw)),
            "inlineStr" => InlineString(cell, formula),
            "b" => new CellValue("boolean", formula, raw, Boolean(raw)),
            "str" => new CellValue("string", formula, raw, raw),
            "e" => new CellValue("error", formula, raw, raw),
            "d" => new CellValue("date", formula, raw, raw),
            "n" => new CellValue("number", formula, raw, raw),
            _ => throw new InvalidDataException($"Unsupported XLSX cell type: {type}"),
        };
    }

    private static CellValue InlineString(XElement cell, string? formula)
    {
        var value = string.Concat(
            cell.Element(Spreadsheet + "is")?
                .Descendants(Spreadsheet + "t")
                .Select(item => item.Value)
            ?? []
        );
        var normalized = Normalize(value);
        return new CellValue("inline-string", formula, normalized, normalized);
    }

    private static string? Boolean(string? value) => value switch
    {
        "0" => "false",
        "1" => "true",
        null => null,
        _ => throw new InvalidDataException($"Invalid XLSX boolean value: {value}"),
    };

    private static string? Normalize(string? value)
    {
        if (value is null)
        {
            return null;
        }
        var normalized = value.Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n')
            .Trim();
        return normalized.Length == 0 ? null : normalized;
    }

    private sealed record CellValue(
        string Kind,
        string? Formula,
        string? Raw,
        string? Display
    );
}
