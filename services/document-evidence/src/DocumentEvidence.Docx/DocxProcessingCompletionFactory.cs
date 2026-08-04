using System.Text.Encodings.Web;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

public static class DocxProcessingCompletionFactory
{
    private const string Configuration =
        "docx-body-v1|normalized-text-v1|semantic-package-fragment-identity-v1";
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static ProcessingCompletionPayload Create(
        Guid revisionId,
        DateTimeOffset completedAt,
        DocxDocument document
    )
    {
        ArgumentNullException.ThrowIfNull(document);
        var manifestJson = JsonSerializer.Serialize(new
        {
            schemaVersion = "1.0",
            document.Adapter,
            document.AdapterVersion,
            document.ArtifactSha256,
            document.PackageEntriesSha256,
            document.IrSha256,
            document.CoreProperties,
            blockCount = document.Blocks.Count,
            configuration = Configuration,
        }, JsonOptions);
        var fragments = document.Blocks
            .Select((block, index) => new ProcessingFragmentWrite(
                OoxmlDeterministicIdentity.CreateGuid(
                    $"{document.PackageEntriesSha256}:{block.BlockId}"
                ),
                revisionId,
                index + 1,
                block.Kind,
                JsonSerializer.Serialize(block.Anchor, JsonOptions),
                block.NormalizedText,
                block.ContentSha256
            ))
            .ToArray();
        return new ProcessingCompletionPayload(
            revisionId,
            completedAt,
            new ProcessingArtifactManifest(
                document.Adapter,
                document.AdapterVersion,
                OoxmlHashing.Sha256(Configuration),
                document.ArtifactSha256,
                document.IrSha256,
                manifestJson,
                OoxmlHashing.Sha256(manifestJson)
            ),
            fragments
        );
    }
}
