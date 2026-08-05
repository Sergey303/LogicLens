namespace KnowledgePilot.LogicLens.DocumentEvidence.Client.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await ClientUploadContractTests.UploadUsesVersionedRouteHeadersAndRawBytesAsync();
        await ClientUploadContractTests.TypedQuotaErrorIsPreservedAsync();
        await ClientReadContractTests.NotFoundDocumentReturnsNullAsync();
        await ClientReadContractTests.FragmentAnchorRemainsTypedJsonAsync();
        Console.WriteLine("Document Evidence generated client contract tests passed.");
        return 0;
    }
}
