using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfDeterminismContractTests
{
    public static async Task ExtractionIsDeterministicAsync()
    {
        var first = await ExtractAsync(new FakePdfProcessRunner());
        var second = await ExtractAsync(new FakePdfProcessRunner());

        TestAssert.Equal(first.Document.IrSha256, second.Document.IrSha256, "IR hash changed.");
        TestAssert.Equal(
            first.Manifest.ConfigurationSha256,
            second.Manifest.ConfigurationSha256,
            "Parser configuration hash changed."
        );
        var firstIds = first.Document.Pages.SelectMany(page => page.Blocks).Select(block => block.BlockId);
        var secondIds = second.Document.Pages.SelectMany(page => page.Blocks).Select(block => block.BlockId);
        TestAssert.True(firstIds.SequenceEqual(secondIds), "Block IDs are not deterministic.");
        TestAssert.Equal("25.03.0", first.Manifest.Version, "Poppler version was not retained.");
    }

    public static async Task AnchorsArePageGroundedAsync()
    {
        var result = await ExtractAsync(new FakePdfProcessRunner());
        TestAssert.Equal(2, result.Document.Pages.Count, "Page count changed.");
        var heading = result.Document.Pages[0].Blocks[0];
        var secondPage = result.Document.Pages[1].Blocks.Single();

        TestAssert.Equal(1, heading.Anchor.PageNumber, "Heading page anchor changed.");
        TestAssert.Equal(1, heading.Anchor.BlockOrdinal, "Heading ordinal changed.");
        TestAssert.Equal(72d, heading.Anchor.BoundingBox.XMin, "Heading bbox changed.");
        TestAssert.Equal(2, heading.Anchor.WordIds.Count, "Heading word provenance changed.");
        TestAssert.Equal("heading", heading.Kind, "Heading classification changed.");
        TestAssert.Equal(2, secondPage.Anchor.PageNumber, "Second-page anchor changed.");
        TestAssert.True(
            secondPage.BlockId.StartsWith("fixture-pdf:p0002:b0001:", StringComparison.Ordinal),
            "Block ID does not encode stable page and ordinal."
        );
    }

    internal static async Task<PdfExtractionResult> ExtractAsync(FakePdfProcessRunner runner)
    {
        var adapter = new PdfPopplerAdapter(runner);
        var result = await adapter.ExtractAsync(
            new MemoryStream(PdfTestFixture.PdfBytes),
            new PdfExtractionRequest(
                "fixture-pdf",
                "https://example.test/fixture.pdf",
                1024
            )
        );
        TestAssert.Equal(3, runner.Calls.Count, "Unexpected Poppler command count.");
        return result;
    }
}
