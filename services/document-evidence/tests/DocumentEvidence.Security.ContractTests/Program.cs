namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await SecureUploadOrderingContractTests.AccessDenialStopsBeforeBodyReadAsync();
        await SecureUploadOrderingContractTests.HourlyQuotaStopsBeforeBodyReadAsync();
        await SecureUploadOrderingContractTests.DeclaredSizeLimitStopsBeforeBodyReadAsync();
        await SecureUploadOrderingContractTests.InvalidSignatureStopsBeforeByteQuotaAsync();
        await SecureUploadOrderingContractTests.DailyByteQuotaStopsBeforeStorageAsync();
        await SecureUploadAcceptanceContractTests.AcceptedUploadNormalizesNameAndAuditsWithoutPathAsync();
        SecureUploadAcceptanceContractTests.DisplayNameRejectsEmptyTraversalAndControlNames();
        await InMemoryQuotaContractTests.HourlyRequestQuotaResetsAtNextUtcHourAsync();
        await InMemoryQuotaContractTests.DailyByteQuotaIsIndependentFromRequestQuotaAsync();
        HmacReadPlanProtectorContractTests.RoundTripPreservesPayloadWithoutStoragePath();
        HmacReadPlanProtectorContractTests.TamperedTokenIsRejected();
        HmacReadPlanProtectorContractTests.TokenSignedByAnotherKeyIsRejected();
        HmacReadPlanProtectorContractTests.ShortSigningKeyIsRejected();
        Console.WriteLine("Document Evidence security contract tests passed.");
        return 0;
    }
}
