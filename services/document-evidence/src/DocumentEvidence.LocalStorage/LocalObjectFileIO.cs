using System.Security.Cryptography;

namespace KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;

internal static class LocalObjectFileIO
{
    private const int BufferSize = 81920;

    public static async Task<long> WriteStagingAsync(
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

    public static bool TryPromote(string stagingPath, string objectPath)
    {
        return AtomicFilePromotion.TryCreateHardLink(stagingPath, objectPath);
    }

    public static async Task DemandContentMatchAsync(
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
        await DemandHashAsync(stream, expectedHash, cancellationToken);
    }

    public static async Task<Stream> OpenVerifiedReadAsync(
        string objectPath,
        string expectedHash,
        CancellationToken cancellationToken
    )
    {
        var stream = OpenReadStream(objectPath);
        try
        {
            await DemandHashAsync(stream, expectedHash, cancellationToken);
            stream.Position = 0;
            return stream;
        }
        catch
        {
            await stream.DisposeAsync();
            throw;
        }
    }

    public static async Task<string> ComputeHashAsync(
        string path,
        CancellationToken cancellationToken
    )
    {
        await using var stream = OpenReadStream(path);
        return await ComputeHashAsync(stream, cancellationToken);
    }

    private static async Task DemandHashAsync(
        Stream stream,
        string expectedHash,
        CancellationToken cancellationToken
    )
    {
        var actualHash = await ComputeHashAsync(stream, cancellationToken);
        if (!string.Equals(actualHash, expectedHash, StringComparison.Ordinal))
        {
            throw new InvalidDataException("Stored object bytes do not match their SHA-256 key.");
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
        Stream stream,
        CancellationToken cancellationToken
    )
    {
        var hash = await SHA256.HashDataAsync(stream, cancellationToken);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }
}
