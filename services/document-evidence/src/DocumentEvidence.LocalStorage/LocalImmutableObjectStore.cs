using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

public sealed class LocalImmutableObjectStore : IImmutableObjectStore
{
    private readonly LocalStoragePaths _paths;

    public LocalImmutableObjectStore(LocalObjectStoreOptions options)
    {
        _paths = new LocalStoragePaths(options);
    }

    public async Task<StoredObjectReference> PutAsync(
        Stream content,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(content);
        if (!content.CanRead)
        {
            throw new ArgumentException("Object content stream must be readable.", nameof(content));
        }

        var stagingPath = _paths.CreateStagingPath();
        try
        {
            var sizeBytes = await LocalObjectFileIO.WriteStagingAsync(
                content,
                stagingPath,
                cancellationToken
            );
            var sha256 = await LocalObjectFileIO.ComputeHashAsync(
                stagingPath,
                cancellationToken
            );
            var address = _paths.Resolve(sha256);
            Directory.CreateDirectory(Path.GetDirectoryName(address.ObjectPath)!);

            var created = LocalObjectFileIO.TryPromote(stagingPath, address.ObjectPath);
            if (!created)
            {
                await LocalObjectFileIO.DemandContentMatchAsync(
                    address.ObjectPath,
                    address.Sha256,
                    sizeBytes,
                    cancellationToken
                );
            }

            return new StoredObjectReference(
                address.Sha256,
                sizeBytes,
                address.ObjectKey,
                created
            );
        }
        finally
        {
            File.Delete(stagingPath);
        }
    }

    public Task<Stream> OpenReadAsync(
        string sha256,
        CancellationToken cancellationToken
    )
    {
        var address = _paths.Resolve(sha256);
        return LocalObjectFileIO.OpenVerifiedReadAsync(
            address.ObjectPath,
            address.Sha256,
            cancellationToken
        );
    }
}
