using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Microsoft.Extensions.DependencyInjection;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal static class GeneratedPackageIdentityTests
{
    public static void ValidReceiptRegistersDiagnosticsAndStore()
    {
        var receiptPath = WriteReceipt(new string('A', 64));
        try
        {
            var identity = GeneratedPackageIdentity.Load(receiptPath);
            var services = new ServiceCollection();
            services.AddAppForgeGeneratedOperationalStore(
                new Uri("https://generated.test/"),
                identity
            );

            using var provider = services.BuildServiceProvider();
            var resolvedIdentity = provider.GetRequiredService<GeneratedPackageIdentity>();
            var store = provider.GetRequiredService<IGeneratedOperationalStore>();

            TestAssert.Equal(new string('a', 64), identity.AppForgeCommit, "Commit was not normalized.");
            TestAssert.True(
                ReferenceEquals(identity, resolvedIdentity),
                "Generated identity was not registered as the diagnostic singleton."
            );
            TestAssert.True(
                store is AppForgeGeneratedOperationalStore,
                "Generated operational store was not registered."
            );
        }
        finally
        {
            File.Delete(receiptPath);
        }
    }

    public static async Task InvalidReceiptFailsBeforeHttpAsync()
    {
        var receiptPath = WriteReceipt("not-a-sha256");
        try
        {
            await TestAssert.ThrowsAsync<InvalidDataException>(
                () => Task.Run(() => GeneratedPackageIdentity.Load(receiptPath)),
                "Invalid receipt hash was accepted."
            );
        }
        finally
        {
            File.Delete(receiptPath);
        }
    }

    private static string WriteReceipt(string appForgeCommit)
    {
        var path = Path.Combine(Path.GetTempPath(), $"logiclens-receipt-{Guid.NewGuid():N}.json");
        var hash = new string('b', 64);
        File.WriteAllText(
            path,
            $$"""
            {
              "kind": "logiclens-appforge-generation-receipt",
              "version": 2,
              "appForgeCommit": "{{appForgeCommit}}",
              "modelId": "Document Evidence Operational Model",
              "projectFileName": "DocumentEvidenceOperationalModel.Persistence.csproj",
              "sourceSpecSha256": "{{hash}}",
              "packageManifestSha256": "{{hash}}",
              "generatedTreeSha256BeforeReceipt": "{{hash}}"
            }
            """
        );
        return path;
    }
}
