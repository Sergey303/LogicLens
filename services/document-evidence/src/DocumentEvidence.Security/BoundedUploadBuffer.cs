namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

internal static class BoundedUploadBuffer
{
    public static async Task<byte[]> ReadAsync(
        Stream source,
        long? declaredLength,
        long maxBytes,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(source);
        if (!source.CanRead)
        {
            throw new ArgumentException("Upload stream must be readable.", nameof(source));
        }
        if (maxBytes < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(maxBytes));
        }
        if (declaredLength is < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(declaredLength));
        }
        if (declaredLength > maxBytes)
        {
            throw new InvalidDataException("Declared upload length exceeds the upload byte limit.");
        }

        using var output = declaredLength is > 0 and <= int.MaxValue
            ? new MemoryStream((int)declaredLength.Value)
            : new MemoryStream();
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
                throw new InvalidDataException("Upload exceeds the upload byte limit.");
            }
            await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken);
        }
        if (declaredLength.HasValue && total != declaredLength.Value)
        {
            throw new InvalidDataException("Upload length differs from the declared length.");
        }
        if (total == 0)
        {
            throw new InvalidDataException("Upload content is empty.");
        }
        return output.ToArray();
    }
}
