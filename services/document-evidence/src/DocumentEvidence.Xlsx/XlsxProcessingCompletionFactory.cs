using System.Text.Encodings.Web;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

public static class XlsxProcessingCompletionFactory
{
    private const string Configuration =
        "xlsx-cells-v1|formula-cached-raw-v1|semantic-package-fragment-identity-v1";
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static ProcessingCompletionPayload Create(
        Guid revisionId,
        DateTimeOffset completedAt,
        XlsxWorkbook workbook
    )
    {
        ArgumentNullException.ThrowIfNull(workbook);
        var cells = workbook.Sheets
            .OrderBy(sheet => sheet.SheetIndex)
            .SelectMany(sheet => sheet.Cells
                .OrderBy(cell => cell.Anchor.RowIndex)
                .ThenBy(cell => cell.Anchor.ColumnIndex))
            .ToArray();
        var manifestJson = JsonSerializer.Serialize(new
        {
            schemaVersion = "1.0",
            workbook.Adapter,
            workbook.AdapterVersion,
            workbook.ArtifactSha256,
            workbook.PackageEntriesSha256,
            workbook.IrSha256,
            workbook.CoreProperties,
            sheetCount = workbook.Sheets.Count,
            cellCount = cells.Length,
            configuration = Configuration,
        }, JsonOptions);
        var fragments = cells
            .Select((cell, index) => new ProcessingFragmentWrite(
                OoxmlDeterministicIdentity.CreateGuid(
                    $"{workbook.PackageEntriesSha256}:{cell.CellId}"
                ),
                revisionId,
                index + 1,
                "worksheet-cell",
                JsonSerializer.Serialize(new
                {
                    cell.Anchor,
                    cell.ValueKind,
                    cell.Formula,
                    cell.RawValue,
                    cell.CachedValue,
                }, JsonOptions),
                cell.DisplayValue ?? cell.RawValue ?? cell.Formula ?? string.Empty,
                cell.ContentSha256
            ))
            .ToArray();
        return new ProcessingCompletionPayload(
            revisionId,
            completedAt,
            new ProcessingArtifactManifest(
                workbook.Adapter,
                workbook.AdapterVersion,
                OoxmlHashing.Sha256(Configuration),
                workbook.ArtifactSha256,
                workbook.IrSha256,
                manifestJson,
                OoxmlHashing.Sha256(manifestJson)
            ),
            fragments
        );
    }
}
