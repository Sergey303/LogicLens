using System.Security.Cryptography;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal static class PdfInputValidator
{
    private static readonly byte[] Magic = "%PDF-"u8.ToArray();

    public static async Task<PdfValidatedInput> ReadAsync(
        Stream source,
        PdfExtractionRequest request,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(source);
        ValidateRequest(request);

        await using var buffer = new MemoryStream();
        var chunk = new byte[81920];
        while (true)
        {
            var read = await source.ReadAsync(chunk, cancellationToken);
            if (read == 0)
            {
                break;
            }
            if (buffer.Length + read > request.MaxBytes)
            {
                throw new InvalidDataException("PDF exceeds the configured byte limit.");
            }
            await buffer.WriteAsync(chunk.AsMemory(0, read), cancellationToken);
        }

        var bytes = buffer.ToArray();
        if (bytes.Length < Magic.Length || !bytes.AsSpan(0, Magic.Length).SequenceEqual(Magic))
        {
            throw new InvalidDataException("PDF magic header is missing.");
        }

        var sha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        if (request.ExpectedSha256 is not null &&
            !string.Equals(request.ExpectedSha256, sha256, StringComparison.Ordinal))
        {
            throw new InvalidDataException("PDF SHA-256 does not match the expected revision.");
        }
        return new PdfValidatedInput(bytes, sha256);
    }

    private static void ValidateRequest(PdfExtractionRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.SourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.SourceUri);
        if (request.MaxBytes is < 1 or > 67_108_864)
        {
            throw new ArgumentOutOfRangeException(nameof(request.MaxBytes));
        }
        if (request.ExpectedSha256 is not null &&
            (request.ExpectedSha256.Length != 64 ||
             request.ExpectedSha256.Any(character => !Uri.IsHexDigit(character))))
        {
            throw new ArgumentException("Expected SHA-256 must be 64 hexadecimal characters.");
        }
    }
}

internal sealed record PdfValidatedInput(byte[] Bytes, string Sha256);
