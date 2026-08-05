namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await PdfValidationContractTests.InvalidSignatureStopsBeforePopplerAsync();
        await PdfValidationContractTests.OversizedInputStopsBeforePopplerAsync();
        await PdfValidationContractTests.HashMismatchStopsBeforePopplerAsync();
        await PdfDeterminismContractTests.ExtractionIsDeterministicAsync();
        await PdfDeterminismContractTests.AnchorsArePageGroundedAsync();
        await PdfRetentionContractTests.OnlySelectedEvidenceIsRetainedAsync();
        await PdfCompletionContractTests.CompletionPayloadIsDeterministicAsync();
        await PdfSourceProposalBridgeContractTests.ExportMatchesSharedSourceFragmentFixtureAsync();
        Console.WriteLine("Document Evidence PDF adapter contract tests passed.");
        return 0;
    }
}
