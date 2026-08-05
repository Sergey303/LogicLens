using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfCompletionContractTests
{
    public static async Task CompletionPayloadIsDeterministicAsync()
    {
        var adapter = new PdfPopplerAdapter(new FakePdfProcessRunner());
        await using var source = new MemoryStream(PdfTestFixture.PdfBytes);
        var extraction = await adapter.ExtractAsync(
            source,
            new PdfExtractionRequest("source-1", "https://example.test/source.pdf", 1024)
        );
        var revisionId = Guid.NewGuid();
        var completedAt = DateTimeOffset.Parse("2026-08-04T15:00:00Z");

        var first = PdfProcessingCompletionFactory.Create(revisionId, completedAt, extraction);
        var second = PdfProcessingCompletionFactory.Create(revisionId, completedAt, extraction);

        TestAssert.Equal(
            first.Manifest.ManifestSha256,
            second.Manifest.ManifestSha256,
            "Parser manifest identity must be deterministic."
        );
        TestAssert.Equal(3, first.Fragments.Count, "Every extracted block must become one fragment.");
        TestAssert.True(
            first.Fragments.Select(item => item.FragmentId)
                .SequenceEqual(second.Fragments.Select(item => item.FragmentId)),
            "Fragment identities must be deterministic."
        );
        TestAssert.True(
            first.Fragments.Select(item => item.Sequence).SequenceEqual([1, 2, 3]),
            "Fragment sequence must be contiguous across pages."
        );
        TestAssert.True(
            first.Fragments[0].AnchorJson.Contains("\"pageNumber\":1", StringComparison.Ordinal),
            "Persisted anchors must retain page provenance."
        );
        TestAssert.Equal(
            extraction.Document.IrSha256,
            first.Manifest.IrSha256,
            "Completion manifest must retain canonical IR identity."
        );
    }
}
