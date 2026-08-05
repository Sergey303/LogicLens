using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public static class PdfProcessingCompletionFactory
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static ProcessingCompletionPayload Create(
        Guid revisionId,
        DateTimeOffset completedAt,
        PdfExtractionResult extraction
    )
    {
        ArgumentNullException.ThrowIfNull(extraction);
        DemandConsistentManifest(extraction);
        var manifestJson = JsonSerializer.Serialize(extraction.Manifest, JsonOptions);
        var fragments = new List<ProcessingFragmentWrite>();
        var sequence = 0;

        foreach (var page in extraction.Document.Pages.OrderBy(item => item.PageNumber))
        {
            foreach (var block in page.Blocks.OrderBy(item => item.ReadingOrder))
            {
                sequence++;
                fragments.Add(new ProcessingFragmentWrite(
                    CreateGuid($"{extraction.Document.Artifact.Sha256}:{block.BlockId}"),
                    revisionId,
                    sequence,
                    block.Kind,
                    JsonSerializer.Serialize(block.Anchor, JsonOptions),
                    block.Text,
                    block.ContentSha256
                ));
            }
        }

        return new ProcessingCompletionPayload(
            revisionId,
            completedAt,
            new ProcessingArtifactManifest(
                extraction.Manifest.Adapter,
                extraction.Manifest.Version,
                extraction.Manifest.ConfigurationSha256,
                extraction.Manifest.ArtifactSha256,
                extraction.Manifest.IrSha256,
                manifestJson,
                Sha256(manifestJson)
            ),
            fragments
        );
    }

    private static void DemandConsistentManifest(PdfExtractionResult extraction)
    {
        if (extraction.Manifest.ArtifactSha256 != extraction.Document.Artifact.Sha256
            || extraction.Manifest.IrSha256 != extraction.Document.IrSha256)
        {
            throw new InvalidDataException("PDF parser manifest does not match extracted artifacts.");
        }
    }

    private static Guid CreateGuid(string identity)
    {
        Span<byte> bytes = stackalloc byte[16];
        SHA256.HashData(Encoding.UTF8.GetBytes(identity)).AsSpan(0, 16).CopyTo(bytes);
        bytes[6] = (byte)((bytes[6] & 0x0f) | 0x50);
        bytes[8] = (byte)((bytes[8] & 0x3f) | 0x80);
        return new Guid(bytes);
    }

    private static string Sha256(string value)
    {
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)))
            .ToLowerInvariant();
    }
}
