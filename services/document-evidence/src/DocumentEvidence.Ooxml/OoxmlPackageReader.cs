using System.IO.Compression;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlPackageReader
{
    public static async Task<OoxmlPackageSnapshot> ReadAsync(
        Stream source,
        OoxmlPackageLimits? limits = null,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(source);
        limits ??= new OoxmlPackageLimits();
        DemandLimits(limits);
        var packageBytes = await ReadBoundedAsync(
            source,
            limits.MaxPackageBytes,
            cancellationToken
        );
        if (packageBytes.Length < 4
            || packageBytes[0] != (byte)'P'
            || packageBytes[1] != (byte)'K'
            || packageBytes[2] != 3
            || packageBytes[3] != 4)
        {
            throw new InvalidDataException("OOXML package ZIP signature is missing.");
        }

        var parts = ReadParts(packageBytes, limits);
        var core = OoxmlCorePropertiesReader.Read(
            parts.GetValueOrDefault("docProps/core.xml")
        );
        var identity = new OoxmlPackageIdentity(
            OoxmlHashing.Sha256(packageBytes),
            OoxmlHashing.EntriesSha256(parts.Values),
            parts.Count,
            parts.Values.Sum(item => item.Content.LongLength),
            core
        );
        return new OoxmlPackageSnapshot(identity, parts);
    }

    private static Dictionary<string, OoxmlPart> ReadParts(
        byte[] packageBytes,
        OoxmlPackageLimits limits
    )
    {
        var parts = new Dictionary<string, OoxmlPart>(StringComparer.OrdinalIgnoreCase);
        long total = 0;
        using var stream = new MemoryStream(packageBytes, writable: false);
        using var archive = new ZipArchive(stream, ZipArchiveMode.Read, leaveOpen: false);
        foreach (var entry in archive.Entries)
        {
            if (entry.Name.Length == 0)
            {
                _ = OoxmlPathPolicy.DemandPartName(entry.FullName.TrimEnd('/'));
                continue;
            }
            var name = OoxmlPathPolicy.DemandPartName(entry.FullName);
            if (parts.Count >= limits.MaxEntries)
            {
                throw new InvalidDataException("OOXML package exceeds the entry limit.");
            }
            if (entry.Length < 0 || entry.Length > limits.MaxEntryBytes)
            {
                throw new InvalidDataException($"OOXML part exceeds its byte limit: {name}");
            }
            total = checked(total + entry.Length);
            if (total > limits.MaxUncompressedBytes)
            {
                throw new InvalidDataException("OOXML package exceeds the uncompressed byte limit.");
            }
            if (parts.ContainsKey(name))
            {
                throw new InvalidDataException($"Duplicate OOXML part name: {name}");
            }
            using var entryStream = entry.Open();
            var content = ReadEntry(entryStream, entry.Length, limits.MaxEntryBytes, name);
            parts.Add(name, new OoxmlPart(name, content, OoxmlHashing.Sha256(content)));
        }
        if (parts.Count == 0)
        {
            throw new InvalidDataException("OOXML package contains no file parts.");
        }
        return parts;
    }

    private static byte[] ReadEntry(
        Stream stream,
        long declaredLength,
        long maxBytes,
        string name
    )
    {
        using var output = new MemoryStream(
            declaredLength <= int.MaxValue ? (int)declaredLength : 0
        );
        var buffer = new byte[81_920];
        long total = 0;
        while (true)
        {
            var read = stream.Read(buffer, 0, buffer.Length);
            if (read == 0)
            {
                break;
            }
            total = checked(total + read);
            if (total > maxBytes)
            {
                throw new InvalidDataException($"OOXML part expands beyond its limit: {name}");
            }
            output.Write(buffer, 0, read);
        }
        if (total != declaredLength)
        {
            throw new InvalidDataException($"OOXML part length changed while reading: {name}");
        }
        return output.ToArray();
    }

    private static async Task<byte[]> ReadBoundedAsync(
        Stream source,
        long maxBytes,
        CancellationToken cancellationToken
    )
    {
        using var output = new MemoryStream();
        var buffer = new byte[81_920];
        long total = 0;
        while (true)
        {
            var read = await source.ReadAsync(buffer, cancellationToken);
            if (read == 0)
            {
                break;
            }
            total = checked(total + read);
            if (total > maxBytes)
            {
                throw new InvalidDataException("OOXML package exceeds the package byte limit.");
            }
            await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken);
        }
        return output.ToArray();
    }

    private static void DemandLimits(OoxmlPackageLimits limits)
    {
        if (limits.MaxPackageBytes < 1
            || limits.MaxEntries < 1
            || limits.MaxEntryBytes < 1
            || limits.MaxUncompressedBytes < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(limits));
        }
    }
}
