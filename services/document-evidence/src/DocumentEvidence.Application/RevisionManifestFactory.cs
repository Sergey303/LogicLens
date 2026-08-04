using System.Buffers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public static class RevisionManifestFactory
{
    public static RevisionManifest Create(
        StoredObjectReference storedObject,
        string mediaType,
        string sourceKind,
        string adapter,
        string adapterVersion
    )
    {
        ArgumentNullException.ThrowIfNull(storedObject);
        DemandSha256(storedObject.Sha256);
        if (storedObject.SizeBytes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(storedObject));
        }

        mediaType = DemandText(mediaType, nameof(mediaType), 200);
        sourceKind = DemandText(sourceKind, nameof(sourceKind), 80);
        adapter = DemandText(adapter, nameof(adapter), 120);
        adapterVersion = DemandText(adapterVersion, nameof(adapterVersion), 80);

        var buffer = new ArrayBufferWriter<byte>();
        using (var writer = new Utf8JsonWriter(buffer))
        {
            writer.WriteStartObject();
            writer.WriteNumber("formatVersion", 1);
            writer.WriteString("objectSha256", storedObject.Sha256);
            writer.WriteNumber("sizeBytes", storedObject.SizeBytes);
            writer.WriteString("mediaType", mediaType);
            writer.WriteString("sourceKind", sourceKind);
            writer.WriteString("adapter", adapter);
            writer.WriteString("adapterVersion", adapterVersion);
            writer.WriteEndObject();
        }

        var canonicalBytes = buffer.WrittenSpan.ToArray();
        var canonicalJson = Encoding.UTF8.GetString(canonicalBytes);
        var manifestHash = Convert.ToHexString(SHA256.HashData(canonicalBytes)).ToLowerInvariant();
        return new RevisionManifest(
            1,
            storedObject.Sha256,
            storedObject.SizeBytes,
            mediaType,
            sourceKind,
            adapter,
            adapterVersion,
            canonicalJson,
            manifestHash
        );
    }

    private static string DemandText(string value, string parameterName, int maxLength)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value, parameterName);
        if (!string.Equals(value, value.Trim(), StringComparison.Ordinal) || value.Length > maxLength)
        {
            throw new ArgumentException(
                $"Value must be trimmed and at most {maxLength} characters.",
                parameterName
            );
        }
        return value;
    }

    private static void DemandSha256(string value)
    {
        if (value.Length != 64 || value.Any(character => !Uri.IsHexDigit(character)))
        {
            throw new ArgumentException("Stored object hash must be SHA-256 hex.", nameof(value));
        }
        if (!string.Equals(value, value.ToLowerInvariant(), StringComparison.Ordinal))
        {
            throw new ArgumentException("Stored object hash must be lowercase.", nameof(value));
        }
    }
}
