namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await AdapterContractTests.FindDocumentMapsExpectedRouteAsync();
        await AdapterContractTests.ListFragmentsValidatesAndPaginatesAsync();
        await AdapterContractTests.WorkspaceMismatchStopsBeforeFragmentLookupAsync();
        Console.WriteLine("Document Evidence generated adapter contract tests passed.");
        return 0;
    }
}
