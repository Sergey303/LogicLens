using KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class XlsxContractTests
{
    public static async Task WorkbookAnchorsAndValuesAreStableAsync()
    {
        var adapter = new XlsxAdapter();
        var first = await ExtractAsync(adapter, XlsxFixture.Build(reverse: false));
        var second = await ExtractAsync(adapter, XlsxFixture.Build(
            reverse: true,
            timestamp: new DateTimeOffset(2025, 3, 3, 0, 0, 0, TimeSpan.Zero)
        ));

        TestAssert.Equal(first.IrSha256, second.IrSha256, "XLSX IR must be deterministic.");
        TestAssert.Equal(
            first.PackageEntriesSha256,
            second.PackageEntriesSha256,
            "XLSX semantic package identity must ignore ZIP ordering and timestamps."
        );
        TestAssert.True(
            first.ArtifactSha256 != second.ArtifactSha256,
            "XLSX raw artifact identity must preserve ZIP-level differences."
        );
        TestAssert.Equal(2, first.Sheets.Count, "Workbook sheet order was not retained.");
        TestAssert.Equal("Input", first.Sheets[0].Name, "First worksheet name is wrong.");
        TestAssert.Equal("Flags", first.Sheets[1].Name, "Second worksheet name is wrong.");

        var shared = DemandCell(first, "Input", "A1");
        TestAssert.Equal("0", shared.RawValue, "Shared-string raw index was lost.");
        TestAssert.Equal("Shared value", shared.DisplayValue, "Shared string was not resolved.");

        var formula = DemandCell(first, "Input", "B1");
        TestAssert.Equal("SUM(1,2)", formula.Formula, "Formula text was not retained.");
        TestAssert.Equal("3", formula.RawValue, "Formula raw value was not retained.");
        TestAssert.Equal("3", formula.CachedValue, "Formula cached value was not separated.");

        var date = DemandCell(first, "Input", "D2");
        TestAssert.Equal(
            "2026-08-04T12:00:00.0000000+00:00",
            date.DisplayValue,
            "XLSX ISO date value was not canonicalized to UTC."
        );
        TestAssert.Equal(2, date.Anchor.RowIndex, "XLSX row anchor is wrong.");
        TestAssert.Equal(4, date.Anchor.ColumnIndex, "XLSX column anchor is wrong.");
    }

    public static async Task ExternalWorksheetRelationshipFailsClosedAsync()
    {
        var relationships = """
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="https://example.com/sheet.xml" TargetMode="External" />
              <Relationship Id="rId2"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet2.xml" />
            </Relationships>
            """;
        var package = OoxmlZipMutation.Replace(
            XlsxFixture.Build(),
            "xl/_rels/workbook.xml.rels",
            relationships
        );
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ExtractAsync(new XlsxAdapter(), package),
            "External worksheet relationships must fail closed."
        );
    }

    public static async Task UnsupportedCellTypeFailsClosedAsync()
    {
        var worksheet = """
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData><row r="1"><c r="A1" t="unknown"><v>x</v></c></row></sheetData>
            </worksheet>
            """;
        var package = OoxmlZipMutation.Replace(
            XlsxFixture.Build(),
            "xl/worksheets/sheet1.xml",
            worksheet
        );
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ExtractAsync(new XlsxAdapter(), package),
            "Unknown XLSX cell types must fail closed."
        );
    }

    private static XlsxCell DemandCell(
        XlsxWorkbook workbook,
        string sheetName,
        string reference
    ) => workbook.Sheets
        .Single(sheet => sheet.Name == sheetName)
        .Cells.Single(cell => cell.Anchor.CellReference == reference);

    private static Task<XlsxWorkbook> ExtractAsync(XlsxAdapter adapter, byte[] content) =>
        adapter.ExtractAsync(new MemoryStream(content, writable: false));
}
