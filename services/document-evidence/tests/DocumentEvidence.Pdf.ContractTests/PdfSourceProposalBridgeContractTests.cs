using System.Text.Json.Nodes;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfSourceProposalBridgeContractTests
{
    private const string Quote =
        "The Product Owner is accountable for maximizing the value of the product.";
    private const string ContentHash =
        "ec27b6c01c6782813eece6fcd504ccdcd996c5e7bfbbd4304f721b8f1b641588";

    public static async Task ExportMatchesSharedSourceFragmentFixtureAsync()
    {
        var blockId = $"document-evidence-pdf:p0001:b0001:{ContentHash[..12]}";
        var evidence = new RetainedPdfEvidence(
            "document-evidence-pdf",
            new string('e', 64),
            "24.02.0",
            [
                new PdfBlock(
                    blockId,
                    1,
                    "paragraph",
                    Quote,
                    Quote,
                    ContentHash,
                    new PdfSourceAnchor(
                        1,
                        1,
                        new PdfBoundingBox(72, 700, 540, 720),
                        ["w0001", "w0002"]
                    )
                ),
            ]
        );

        var actual = PdfSourceProposalBridge.ExportJsonLines(
            "document-evidence-pdf-v1",
            $"sha256:{new string('f', 64)}",
            evidence
        );
        var expected = await File.ReadAllBytesAsync(
            Path.Combine(AppContext.BaseDirectory, "pdf-source-proposal-fragment-v1.jsonl")
        );

        var actualNode = JsonNode.Parse(actual)
            ?? throw new InvalidDataException("Bridge output is not JSON.");
        var expectedNode = JsonNode.Parse(expected)
            ?? throw new InvalidDataException("Shared bridge fixture is not JSON.");
        TestAssert.True(
            JsonNode.DeepEquals(expectedNode, actualNode),
            "C# bridge output must remain compatible with the shared source fragment fixture."
        );
    }
}
