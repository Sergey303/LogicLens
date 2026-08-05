using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Docx;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class EngDocLocalDocxGate
{
    private const string ExpectedArtifactSha256 =
        "bbd051dce7fd1e351175677c2c4c5bb8f14e2ba96c5a0f63298dd3a2f318023c";
    private const string SnapshotHash =
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

    public static async Task VerifyAsync(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        await using var stream = File.OpenRead(path);
        var document = await new DocxAdapter().ExtractAsync(stream);

        TestAssert.Equal(
            ExpectedArtifactSha256,
            document.ArtifactSha256,
            "Committed EngDoc DOCX bytes do not match the accepted manifest."
        );
        TestAssert.Equal(
            "EngDoc Sentinel",
            document.CoreProperties.Creator,
            "EngDoc DOCX creator provenance was not retained."
        );
        TestAssert.True(
            document.Blocks.Count >= 20,
            "EngDoc DOCX produced too few canonical blocks."
        );
        var text = document.Blocks.Select(block => block.NormalizedText).ToHashSet(
            StringComparer.Ordinal
        );
        foreach (var expected in new[]
        {
            "Техническая спецификация",
            "Модель изделия: EDS-DEMO-24-120",
            "Входное напряжение: 230 V AC",
            "Номинальная мощность: 120 W",
        })
        {
            TestAssert.True(text.Contains(expected), $"EngDoc DOCX text was not retained: {expected}");
        }

        var selected = document.Blocks.Single(block =>
            block.NormalizedText == "Номинальная мощность: 120 W"
        );
        var evidence = DocxEvidenceSelector.Select(
            document,
            "document-evidence-docx",
            new[] { selected.BlockId }
        );
        var jsonLines = OoxmlSourceProposalBridge.ExportJsonLines(
            "document-evidence-docx-v1",
            SnapshotHash,
            evidence
        );
        using var row = JsonDocument.Parse(jsonLines);
        TestAssert.Equal(
            "Номинальная мощность: 120 W",
            row.RootElement.GetProperty("text").GetString(),
            "Selected EngDoc DOCX evidence changed."
        );
        TestAssert.Equal(
            "docx",
            row.RootElement.GetProperty("sourceAnchor").GetProperty("format").GetString(),
            "Selected EngDoc DOCX anchor format is missing."
        );
        TestAssert.Equal(1, evidence.Fragments.Count, "Unselected EngDoc DOCX blocks leaked.");
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            schemaVersion = "0.1",
            sourcePath = Path.GetFullPath(path),
            document.ArtifactSha256,
            document.PackageEntriesSha256,
            document.IrSha256,
            blockCount = document.Blocks.Count,
            selectedBlockId = selected.BlockId,
            selected.ContentSha256,
            status = "passed",
        }));
    }
}
