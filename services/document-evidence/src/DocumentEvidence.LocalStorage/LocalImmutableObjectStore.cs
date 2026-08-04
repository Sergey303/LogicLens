using System.Security.Cryptography;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

public sealed class LocalImmutableObjectStore : IImmutableObjectStore
{
    private const int BufferSize = 81920;
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
            var sizeBytes = await WriteStagingAsync(content, stagingPath, cancellationToken);
            var sha256 = await ComputeHashAsync(stagingPath, cancellationToken);
            var address = _paths.Resolve(sha256);
            Directory.CreateDirectory(Path.GetDirectoryName(address.ObjectPath)!);

            var created = TryPromote(stagingPath, address.ObjectPath);
            if (!created)
            {
                await DemandContentMatchAsync(
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

    public async Task<Stream> OpenReadAsync(
        string sha256,
        CancellationToken cancellationToken
    )
    {
        var address = _paths.Resolve(sha256);
        var stream = OpenReadStream(address.ObjectPath);
        try
        {
            var actualHash = await ComputeHashAsync(stream, cancellationToken);
            if (!string.Equals(actualHash, address.Sha256, StringComparison.Ordinal))
            {
                throw new InvalidDataException("Stored object bytes do not match their SHA-256 key.");
            }
            stream.Position = 0;
            return stream;
        }
        catch
        {
            await stream.DisposeAsync();
            throw;
        }
    }

    private static async Task<long> WriteStagingAsync(
        Stream source,
        string stagingPath,
        CancellationToken cancellationToken
    )
    {
        await using var target = new FileStream(
            stagingPath,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            BufferSize,
            FileOptions.Asynchronous | FileOptions.SequentialScan
        );
        await source.CopyToAsync(target, cancellationToken);
        await target.FlushAsync(cancellationToken);
        target.Flush(flushToDisk: true);
        return target.Length;
    }

    private static bool TryPromote(string stagingPath, string objectPath)
    {
        try
        {
            File.Move(stagingPath, objectPath, overwrite: false);
            return true;
        }
        catch (IOException) when (File.Exists(objectPath))
        {
            return false;
        }
    }

    private static async Task DemandContentMatchAsync(
        string objectPath,
        string expectedHash,
        long expectedSize,
        CancellationToken cancellationToken
    )
    {
        await using var stream = OpenReadStream(objectPath);
        if (stream.Length != expectedSize)
        {
            throw new InvalidDataException("Existing immutable object has an unexpected size.");
        }
        var actualHash = await ComputeHashAsync(stream, cancellationToken);
        if (!string.Equals(actualHash, expectedHash, StringComparison.Ordinal))
        {
            throw new InvalidDataException("Existing immutable object has unexpected bytes.");
        }
    }

    private static FileStream OpenReadStream(string objectPath)
    {
        return new FileStream(
            objectPath,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            BufferSize,
            FileOptions.Asynchronous | FileOptions.SequentialScan
        );
    }

    private static async Task<string> ComputeHashAsync(
        string path,
        CancellationToken cancellationToken
    )
    {
        await using var stream = OpenReadStream(path);
        return await ComputeHashAsync(stream, cancellationToken);
    }

    private static async Task<string> ComputeHashAsync(
        Stream stream,
        CancellationToken cancellationToken
    )
    {
        var hash = await SHA256.HashDataAsync(stream, cancellationToken);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }
}
