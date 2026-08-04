using System.Security.Cryptography;
using System.Text;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage.ContractTests;

internal static class LocalObjectStoreContractTests
{
    private static readonly byte[] Payload = Encoding.UTF8.GetBytes("immutable evidence bytes");

    public static async Task PutIsContentAddressedAndIdempotentAsync()
    {
        using var root = new TemporaryStorageRoot();
        var store = CreateStore(root.RootPath);

        var first = await PutAsync(store, Payload);
        var second = await PutAsync(store, Payload);
        var expectedHash = Convert.ToHexString(SHA256.HashData(Payload)).ToLowerInvariant();

        TestAssert.Equal(expectedHash, first.Sha256, "Stored hash is incorrect.");
        TestAssert.Equal(first.Sha256, second.Sha256, "Duplicate write changed the hash.");
        TestAssert.Equal(first.ObjectKey, second.ObjectKey, "Duplicate write changed the key.");
        TestAssert.True(first.Created, "First write was not marked as created.");
        TestAssert.True(!second.Created, "Duplicate write was not deduplicated.");
        TestAssert.True(
            first.ObjectKey.EndsWith(first.Sha256, StringComparison.Ordinal),
            "Object key is not derived from SHA-256."
        );

        var physicalPath = root.ResolveObjectKey(first.ObjectKey);
        TestAssert.True(File.Exists(physicalPath), "Content-addressed file was not created.");
        await using var stream = await store.OpenReadAsync(first.Sha256, CancellationToken.None);
        using var memory = new MemoryStream();
        await stream.CopyToAsync(memory);
        TestAssert.True(Payload.SequenceEqual(memory.ToArray()), "Stored bytes changed.");
    }

    public static async Task ConcurrentWritesConvergeAsync()
    {
        using var root = new TemporaryStorageRoot();
        var store = CreateStore(root.RootPath);
        var writes = Enumerable.Range(0, 6)
            .Select(_ => PutAsync(store, Payload))
            .ToArray();

        var results = await Task.WhenAll(writes);

        TestAssert.Equal(1, results.Count(result => result.Created), "Concurrent writes created duplicates.");
        TestAssert.Equal(1, results.Select(result => result.Sha256).Distinct().Count(), "Hashes diverged.");
        TestAssert.Equal(1, results.Select(result => result.ObjectKey).Distinct().Count(), "Keys diverged.");
    }

    private static LocalImmutableObjectStore CreateStore(string rootPath)
    {
        return new LocalImmutableObjectStore(new LocalObjectStoreOptions(rootPath));
    }

    private static Task<StoredObjectReference> PutAsync(
        LocalImmutableObjectStore store,
        byte[] payload
    )
    {
        return store.PutAsync(new MemoryStream(payload, writable: false), CancellationToken.None);
    }
}
