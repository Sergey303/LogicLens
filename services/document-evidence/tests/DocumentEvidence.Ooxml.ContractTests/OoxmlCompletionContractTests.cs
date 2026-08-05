using KnowledgePilot.LogicLens.DocumentEvidence.Docx;
using KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class OoxmlCompletionContractTests
{
    private static readonly Guid RevisionId =
        Guid.Parse("b7f9f7ef-1b7f-4ed3-b3e2-8f416ed3d4b2");
    private static readonly DateTimeOffset CompletedAt =
        DateTimeOffset.Parse("2026-08-04T20:00:00Z");

    public static async Task DocxCompletionUsesSemanticFragmentIdentityAsync()
    {
        var adapter = new DocxAdapter();
        var firstDocument = await adapter.ExtractAsync(new MemoryStream(
            DocxFixture.Build(reverse: false),
            writable: false
        ));
        var secondDocument = await adapter.ExtractAsync(new MemoryStream(
            DocxFixture.Build(
                reverse: true,
                timestamp: new DateTimeOffset(2025, 4, 4, 0, 0, 0, TimeSpan.Zero)
            ),
            writable: false
        ));
        var first = DocxProcessingCompletionFactory.Create(
            RevisionId,
            CompletedAt,
            firstDocument
        );
        var second = DocxProcessingCompletionFactory.Create(
            RevisionId,
            CompletedAt,
            secondDocument
        );

        AssertStableSemanticCompletion(first, second, "DOCX");
        TestAssert.Equal(
            "First paragraph",
            first.Fragments[0].Text,
            "DOCX completion must persist normalized text."
        );
    }

    public static async Task XlsxCompletionRetainsFormulaProvenanceAsync()
    {
        var adapter = new XlsxAdapter();
        var firstWorkbook = await adapter.ExtractAsync(new MemoryStream(
            XlsxFixture.Build(reverse: false),
            writable: false
        ));
        var secondWorkbook = await adapter.ExtractAsync(new MemoryStream(
            XlsxFixture.Build(
                reverse: true,
                timestamp: new DateTimeOffset(2025, 5, 5, 0, 0, 0, TimeSpan.Zero)
            ),
            writable: false
        ));
        var first = XlsxProcessingCompletionFactory.Create(
            RevisionId,
            CompletedAt,
            firstWorkbook
        );
        var second = XlsxProcessingCompletionFactory.Create(
            RevisionId,
            CompletedAt,
            secondWorkbook
        );

        AssertStableSemanticCompletion(first, second, "XLSX");
        var formulaFragment = first.Fragments.Single(item =>
            item.AnchorJson.Contains("SUM(1,2)", StringComparison.Ordinal)
        );
        TestAssert.Equal("3", formulaFragment.Text, "Cached formula value was not persisted.");
        TestAssert.True(
            formulaFragment.AnchorJson.Contains("\"rawValue\":\"3\"", StringComparison.Ordinal)
                && formulaFragment.AnchorJson.Contains(
                    "\"cachedValue\":\"3\"",
                    StringComparison.Ordinal
                ),
            "XLSX completion must retain raw and cached formula values."
        );
    }

    private static void AssertStableSemanticCompletion(
        KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts.ProcessingCompletionPayload first,
        KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts.ProcessingCompletionPayload second,
        string format
    )
    {
        TestAssert.True(
            first.Manifest.ArtifactSha256 != second.Manifest.ArtifactSha256,
            $"{format} manifest must preserve raw ZIP differences."
        );
        TestAssert.Equal(
            first.Manifest.IrSha256,
            second.Manifest.IrSha256,
            $"{format} semantic IR must remain stable."
        );
        TestAssert.Equal(
            first.Fragments.Count,
            second.Fragments.Count,
            $"{format} fragment count changed."
        );
        for (var index = 0; index < first.Fragments.Count; index++)
        {
            TestAssert.Equal(index + 1, first.Fragments[index].Sequence, "Sequence is not contiguous.");
            TestAssert.Equal(
                first.Fragments[index].FragmentId,
                second.Fragments[index].FragmentId,
                $"{format} fragment identity depends on ZIP container bytes."
            );
            TestAssert.Equal(
                first.Fragments[index].ContentHash,
                second.Fragments[index].ContentHash,
                $"{format} canonical content changed."
            );
        }
    }
}
