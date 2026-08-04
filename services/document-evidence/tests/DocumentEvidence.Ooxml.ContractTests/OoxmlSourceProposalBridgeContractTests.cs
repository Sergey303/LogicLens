using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Docx;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;
using KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class OoxmlSourceProposalBridgeContractTests
{
    private const string SnapshotHash =
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

    public static async Task RealXlsxSelectionMatchesSharedFixtureAsync()
    {
        var workbookPath = Path.Combine(
            AppContext.BaseDirectory,
            "fixtures",
            "engdoc-confirmed-package-checklist.xlsx"
        );
        await using var stream = File.OpenRead(workbookPath);
        var workbook = await new XlsxAdapter().ExtractAsync(stream);
        var cell = workbook.Sheets.Single()
            .Cells.Single(item => item.Anchor.CellReference == "D9");
        var evidence = XlsxEvidenceSelector.Select(
            workbook,
            "document-evidence-xlsx",
            new[] { cell.CellId }
        );
        var actual = OoxmlSourceProposalBridge.ExportJsonLines(
            "document-evidence-xlsx-v1",
            SnapshotHash,
            evidence
        );
        var expected = await File.ReadAllBytesAsync(Path.Combine(
            AppContext.BaseDirectory,
            "fixtures",
            "xlsx-source-proposal-fragment-v1.jsonl"
        ));

        TestAssert.True(
            actual.AsSpan().SequenceEqual(expected),
            "C# XLSX source-fragment export drifted from the shared fixture."
        );
        TestAssert.Equal(1, evidence.Fragments.Count, "Selection retained extra XLSX cells.");
        TestAssert.Equal("Confirmed", evidence.Fragments[0].Text, "Selected cell text changed.");
    }

    public static async Task DocxSelectionRetainsOnlyRequestedBlockAsync()
    {
        var document = await new DocxAdapter().ExtractAsync(new MemoryStream(
            DocxFixture.Build(),
            writable: false
        ));
        var selectedBlock = document.Blocks.Single(item => item.NormalizedText == "Cell B");
        var evidence = DocxEvidenceSelector.Select(
            document,
            "document-evidence-docx",
            new[] { selectedBlock.BlockId }
        );
        var bytes = OoxmlSourceProposalBridge.ExportJsonLines(
            "document-evidence-docx-v1",
            SnapshotHash,
            evidence
        );
        using var json = JsonDocument.Parse(bytes);
        var row = json.RootElement;

        TestAssert.Equal("Cell B", row.GetProperty("text").GetString(), "DOCX text changed.");
        TestAssert.Equal(
            "docx",
            row.GetProperty("sourceAnchor").GetProperty("format").GetString(),
            "DOCX anchor format is missing."
        );
        TestAssert.Equal(1, evidence.Fragments.Count, "Selection retained extra DOCX blocks.");
        TestAssert.True(
            !row.GetRawText().Contains("Cell A", StringComparison.Ordinal),
            "Unselected DOCX content leaked into retained evidence."
        );
    }
}
