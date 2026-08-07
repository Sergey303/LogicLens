namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await ApiEndpointContractTests.GeneratedClientTraversesRealEndpointsAsync();
        await ApiEndpointContractTests.ReadPlanTraversesHeaderOnlyStreamingBoundaryAsync();
        await ApiEndpointContractTests.ReadPlanResponsesAreNeverCacheableAsync();
        await ReadPlanHttpNegativeContractTests.MissingTokenStopsBeforeOperationAsync();
        await ReadPlanHttpNegativeContractTests.OversizedTokenStopsBeforeOperationAsync();
        await ApiEndpointContractTests.MissingActorHeaderReturnsTypedBadRequestAsync();
        Console.WriteLine("Document Evidence real HTTP contract tests passed.");
        return 0;
    }
}
