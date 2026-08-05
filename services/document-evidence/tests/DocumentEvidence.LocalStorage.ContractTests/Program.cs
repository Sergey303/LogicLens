namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await LocalObjectStoreContractTests.PutIsContentAddressedAndIdempotentAsync();
        await LocalObjectStoreContractTests.ConcurrentWritesConvergeAsync();
        await LocalObjectStoreSecurityTests.CorruptionIsDetectedAsync();
        await LocalObjectStoreSecurityTests.InvalidHashIsRejectedAsync();
        LocalObjectStoreSecurityTests.WebRootOverlapIsRejected();
        Console.WriteLine("Document Evidence local storage contract tests passed.");
        return 0;
    }
}
