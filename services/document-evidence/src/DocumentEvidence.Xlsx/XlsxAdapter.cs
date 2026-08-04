using System.Text.Json;
using System.Xml.Linq;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

public sealed class XlsxAdapter
{
    private const string AdapterName = "xlsx-ooxml";
    private const string AdapterVersion = "1.0.0";
    private const string OfficeDocumentRelationship =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument";
    private const string WorksheetRelationship =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet";
    private const string SharedStringsRelationship =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings";
    private const string WorkbookContentType =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml";
    private const string WorksheetContentType =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml";
    private static readonly XNamespace Spreadsheet =
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    private static readonly XNamespace OfficeRelationships =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships";

    public async Task<XlsxWorkbook> ExtractAsync(
        Stream source,
        OoxmlPackageLimits? limits = null,
        CancellationToken cancellationToken = default
    )
    {
        var package = await OoxmlPackageReader.ReadAsync(source, limits, cancellationToken);
        var rootRelationships = OoxmlRelationships.Read(package, "_rels/.rels", "");
        var workbookPartName = OoxmlRelationships.DemandSingleTargetByType(
            rootRelationships,
            OfficeDocumentRelationship
        );
        OoxmlContentTypes.DemandOverride(package, workbookPartName, WorkbookContentType);
        var workbookRelationships = OoxmlRelationships.Read(
            package,
            RelationshipPart(workbookPartName),
            workbookPartName
        );
        var sharedStringsPart = workbookRelationships
            .SingleOrDefault(item => item.Type == SharedStringsRelationship)?
            .TargetPart;
        var sharedStrings = XlsxSharedStrings.Read(
            sharedStringsPart is null ? null : package.RequirePart(sharedStringsPart)
        );
        var sheets = ParseSheets(
            package,
            workbookPartName,
            workbookRelationships,
            sharedStrings
        );
        if (sheets.Count == 0 || sheets.Sum(item => item.Cells.Count) == 0)
        {
            throw new InvalidDataException("XLSX contains no usable worksheet cells.");
        }
        var irHash = OoxmlHashing.Sha256(JsonSerializer.SerializeToUtf8Bytes(new
        {
            adapter = AdapterName,
            version = AdapterVersion,
            package = package.Identity.EntriesSha256,
            metadata = package.Identity.CoreProperties,
            sheets,
        }));
        return new XlsxWorkbook(
            AdapterName,
            AdapterVersion,
            package.Identity.ArtifactSha256,
            package.Identity.EntriesSha256,
            irHash,
            package.Identity.CoreProperties,
            sheets
        );
    }

    private static IReadOnlyList<XlsxSheet> ParseSheets(
        OoxmlPackageSnapshot package,
        string workbookPartName,
        IReadOnlyList<OoxmlRelationship> relationships,
        IReadOnlyList<string> sharedStrings
    )
    {
        var document = OoxmlXml.Parse(package.RequirePart(workbookPartName));
        var relationshipById = relationships.ToDictionary(item => item.Id, StringComparer.Ordinal);
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var result = new List<XlsxSheet>();
        var sheetIndex = 0;
        foreach (var sheet in document.Descendants(Spreadsheet + "sheet"))
        {
            sheetIndex++;
            var name = DemandAttribute(sheet, "name");
            var relationshipId = ((string?)sheet.Attribute(OfficeRelationships + "id"))?.Trim()
                ?? throw new InvalidDataException("XLSX sheet relationship ID is missing.");
            if (!names.Add(name))
            {
                throw new InvalidDataException($"Duplicate XLSX sheet name: {name}");
            }
            if (!relationshipById.TryGetValue(relationshipId, out var relationship)
                || relationship.Type != WorksheetRelationship)
            {
                throw new InvalidDataException($"XLSX worksheet relationship is invalid: {relationshipId}");
            }
            OoxmlContentTypes.DemandOverride(
                package,
                relationship.TargetPart,
                WorksheetContentType
            );
            result.Add(XlsxWorksheetParser.Parse(
                package.RequirePart(relationship.TargetPart),
                sheetIndex,
                name,
                sharedStrings
            ));
        }
        return result;
    }

    private static string RelationshipPart(string sourcePart)
    {
        var separator = sourcePart.LastIndexOf('/');
        var directory = separator < 0 ? "" : sourcePart[..(separator + 1)];
        var fileName = separator < 0 ? sourcePart : sourcePart[(separator + 1)..];
        return $"{directory}_rels/{fileName}.rels";
    }

    private static string DemandAttribute(XElement element, string name)
    {
        var value = ((string?)element.Attribute(name))?.Trim();
        return string.IsNullOrWhiteSpace(value)
            ? throw new InvalidDataException($"XLSX attribute is missing: {name}")
            : value;
    }
}
