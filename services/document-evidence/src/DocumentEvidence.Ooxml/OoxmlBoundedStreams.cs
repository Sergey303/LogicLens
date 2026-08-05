namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

internal static class OoxmlBoundedStreams
{
    public static async Task<byte[]> ReadPackageAsync(
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

    public static byte[] ReadPart(
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
}
