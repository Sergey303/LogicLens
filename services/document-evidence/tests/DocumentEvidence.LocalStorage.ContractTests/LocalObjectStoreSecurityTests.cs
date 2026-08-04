using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage.ContractTests;

internal static class LocalObjectStoreSecurityTests
{
    public static async Task CorruptionIsDetectedAsync()
    {
        using var root = new TemporaryStorageRoot();
        var store = new LocalImmutableObjectStore(new LocalObjectStoreOptions(root.RootPath));
        var payload = Encoding.UTF8.GetBytes("trusted evidence");
        var stored = await store.PutAsync(
            new MemoryStream(payload, writable: false),
            CancellationToken.None
        );
        await File.WriteAllTextAsync(root.ResolveObjectKey(stored.ObjectKey), "tampered");

        await TestAssert.ThrowsAsync<InvalidDataException>(
            async () =>
            {
                await using var ignored = await store.OpenReadAsync(
                    stored.Sha256,
                    CancellationToken.None
                );
            },
            "Corrupted content-addressed bytes were accepted."
        );

        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => store.PutAsync(
                new MemoryStream(payload, writable: false),
                CancellationToken.None
            ),
            "Duplicate write accepted a corrupted existing object."
        );
    }

    public static async Task InvalidHashIsRejectedAsync()
    {
        using var root = new TemporaryStorageRoot();
        var store = new LocalImmutableObjectStore(new LocalObjectStoreOptions(root.RootPath));

        await TestAssert.ThrowsAsync<ArgumentException>(
            async () =>
            {
                await using var ignored = await store.OpenReadAsync(
                    "../../outside",
                    CancellationToken.None
                );
            },
            "Traversal-shaped hash was accepted."
        );
    }

    public static void WebRootOverlapIsRejected()
    {
        using var root = new TemporaryStorageRoot();
        var webRoot = Path.Combine(root.RootPath, "wwwroot");
        var storageRoot = Path.Combine(webRoot, "evidence");
        Directory.CreateDirectory(webRoot);

        TestAssert.Throws<ArgumentException>(
            () => new LocalImmutableObjectStore(
                new LocalObjectStoreOptions(storageRoot, webRoot)
            ),
            "Storage inside webroot was accepted."
        );
    }
}
