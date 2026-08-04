using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfRetentionContractTests
{
    public static async Task OnlySelectedEvidenceIsRetainedAsync()
    {
        var result = await PdfDeterminismContractTests.ExtractAsync(new FakePdfProcessRunner());
        var allBlocks = result.Document.Pages.SelectMany(page => page.Blocks).ToList();
        var selectedId = allBlocks[1].BlockId;

        var retained = PdfEvidenceSelector.Select(result, [selectedId]);

        TestAssert.Equal(1, retained.Blocks.Count, "Retention included unselected evidence.");
        TestAssert.Equal(selectedId, retained.Blocks[0].BlockId, "Retention changed block identity.");
        TestAssert.Equal(
            result.Document.Artifact.Sha256,
            retained.ArtifactSha256,
            "Retention lost source fingerprint."
        );
        TestAssert.True(
            retained.Blocks.All(block => block.BlockId != allBlocks[0].BlockId),
            "Full source evidence leaked into selected retention."
        );
    }
}
