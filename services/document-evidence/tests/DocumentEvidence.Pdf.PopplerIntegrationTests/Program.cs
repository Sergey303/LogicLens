using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.PopplerIntegrationTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        var bytes = MinimalPdfFixture.Create();
        var first = await ExtractAsync(bytes);
        var second = await ExtractAsync(bytes);
        var blocks = first.Document.Pages.SelectMany(page => page.Blocks).ToList();
        var combined = string.Join('\n', blocks.Select(block => block.NormalizedText));

        Demand(first.Document.Pages.Count == 1, "Poppler page count changed.");
        Demand(blocks.Count > 0, "Poppler produced no page-grounded blocks.");
        Demand(combined.Contains("Evidence Heading", StringComparison.Ordinal), "Heading text missing.");
        Demand(combined.Contains("grounded paragraph", StringComparison.Ordinal), "Paragraph text missing.");
        Demand(blocks.All(block => block.Anchor.PageNumber == 1), "Page anchors changed.");
        Demand(blocks.All(block => block.Anchor.BoundingBox.XMax > block.Anchor.BoundingBox.XMin), "Invalid bbox.");
        Demand(first.Manifest.Version != "unknown", "Poppler version was not captured.");
        Demand(first.Document.IrSha256 == second.Document.IrSha256, "Real Poppler IR is not deterministic.");

        var retained = PdfEvidenceSelector.Select(first, [blocks[0].BlockId]);
        Demand(retained.Blocks.Count == 1, "Selected evidence retention leaked full IR.");
        Console.WriteLine(
            $"Document Evidence Poppler integration passed: version={first.Manifest.Version}, " +
            $"blocks={blocks.Count}, ir={first.Document.IrSha256}"
        );
        return 0;
    }

    private static Task<PdfExtractionResult> ExtractAsync(byte[] bytes)
    {
        return new PdfPopplerAdapter(new SystemPdfProcessRunner()).ExtractAsync(
            new MemoryStream(bytes),
            new PdfExtractionRequest(
                "minimal-pdf",
                "https://example.test/minimal.pdf",
                1_048_576
            )
        );
    }

    private static void Demand(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
