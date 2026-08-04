using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

public static class XlsxEvidenceSelector
{
    private static readonly JsonSerializerOptions JsonOptions =
        new(JsonSerializerDefaults.Web);

    public static RetainedOoxmlEvidence Select(
        XlsxWorkbook workbook,
        string sourceId,
        IReadOnlyCollection<string> cellIds
    )
    {
        ArgumentNullException.ThrowIfNull(workbook);
        ArgumentNullException.ThrowIfNull(cellIds);
        var requested = DemandUniqueSelection(cellIds);
        var selected = workbook.Sheets
            .OrderBy(sheet => sheet.SheetIndex)
            .SelectMany(sheet => sheet.Cells
                .OrderBy(cell => cell.Anchor.RowIndex)
                .ThenBy(cell => cell.Anchor.ColumnIndex))
            .Where(cell => requested.Remove(cell.CellId))
            .Select(cell => new OoxmlSelectedFragment(
                cell.CellId,
                "worksheet-cell",
                cell.DisplayValue ?? cell.RawValue ?? cell.Formula ?? string.Empty,
                cell.ContentSha256,
                JsonSerializer.SerializeToElement(new
                {
                    format = "xlsx",
                    cell.Anchor.SheetIndex,
                    cell.Anchor.SheetName,
                    cell.Anchor.RowIndex,
                    cell.Anchor.ColumnIndex,
                    cell.Anchor.CellReference,
                    cell.ValueKind,
                    cell.Formula,
                    cell.RawValue,
                    cell.CachedValue,
                }, JsonOptions),
                new[] { cell.Anchor.SheetName }
            ))
            .ToArray();
        DemandAllFound(requested);
        return new RetainedOoxmlEvidence(
            sourceId,
            workbook.ArtifactSha256,
            workbook.Adapter,
            workbook.AdapterVersion,
            selected
        );
    }

    private static HashSet<string> DemandUniqueSelection(IReadOnlyCollection<string> cellIds)
    {
        if (cellIds.Count == 0)
        {
            throw new ArgumentException("At least one XLSX cell is required.", nameof(cellIds));
        }
        var requested = new HashSet<string>(cellIds, StringComparer.Ordinal);
        if (requested.Count != cellIds.Count)
        {
            throw new ArgumentException("XLSX cell IDs must be unique.", nameof(cellIds));
        }
        return requested;
    }

    private static void DemandAllFound(HashSet<string> remaining)
    {
        if (remaining.Count > 0)
        {
            throw new KeyNotFoundException(
                $"Unknown XLSX cell IDs: {string.Join(", ", remaining)}"
            );
        }
    }
}
