using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public static class PdfSourceProposalBridge
{
    private const int MaxFragmentChars = 7000;
    private static readonly Regex SafeId = new(
        "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly Regex DomainHash = new(
        "^sha256:[0-9a-f]{64}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static byte[] ExportJsonLines(
        string proposalId,
        string snapshotHash,
        RetainedPdfEvidence evidence
    )
    {
        ArgumentNullException.ThrowIfNull(evidence);
        DemandSafeId(proposalId, nameof(proposalId));
        DemandSafeId(evidence.SourceId, nameof(evidence.SourceId));
        if (!DomainHash.IsMatch(snapshotHash))
        {
            throw new ArgumentException("Snapshot hash must use sha256:<lowercase hex>.", nameof(snapshotHash));
        }
        if (evidence.Blocks.Count == 0 || evidence.Blocks.Select(item => item.BlockId).Distinct().Count() != evidence.Blocks.Count)
        {
            throw new InvalidDataException("Retained PDF evidence must contain unique selected blocks.");
        }

        var output = new StringBuilder();
        var headingPath = new List<string>();
        var ordinal = 0;
        foreach (var block in evidence.Blocks
            .OrderBy(item => item.Anchor.PageNumber)
            .ThenBy(item => item.ReadingOrder))
        {
            DemandBlock(block);
            if (block.Kind == "heading")
            {
                headingPath = [block.NormalizedText];
            }
            var chunks = Chunk(block.NormalizedText);
            for (var chunkIndex = 0; chunkIndex < chunks.Count; chunkIndex++)
            {
                ordinal++;
                var suffix = chunks.Count > 1 ? $":c{chunkIndex + 1:000}" : "";
                var fragmentId = $"{evidence.SourceId}#p-{block.Anchor.PageNumber:0000}-b-{block.Anchor.BlockOrdinal:0000}{suffix}";
                var row = new
                {
                    schemaVersion = "0.1",
                    fragmentId,
                    proposalId,
                    sourceId = evidence.SourceId,
                    snapshotHash,
                    ordinal,
                    headingPath = headingPath.ToArray(),
                    lineStart = 1,
                    lineEnd = chunks[chunkIndex].Count(character => character == '\n') + 1,
                    pageNumber = block.Anchor.PageNumber,
                    blockIds = new[] { block.BlockId },
                    sourceAnchor = new
                    {
                        block.Anchor.PageNumber,
                        block.Anchor.BlockOrdinal,
                        block.Anchor.BoundingBox,
                        wordIds = block.Anchor.WordIds,
                    },
                    processor = new
                    {
                        name = "poppler-bbox-layout",
                        version = evidence.ParserVersion,
                        artifactSha256 = $"sha256:{evidence.ArtifactSha256}",
                    },
                    text = chunks[chunkIndex],
                    textHash = $"sha256:{PdfHashing.Sha256(chunks[chunkIndex])}",
                };
                output.Append(JsonSerializer.Serialize(row, JsonOptions)).Append('\n');
            }
        }
        return Encoding.UTF8.GetBytes(output.ToString());
    }

    private static IReadOnlyList<string> Chunk(string text)
    {
        var chunks = new List<string>();
        for (var offset = 0; offset < text.Length; offset += MaxFragmentChars)
        {
            chunks.Add(text.Substring(offset, Math.Min(MaxFragmentChars, text.Length - offset)));
        }
        return chunks;
    }

    private static void DemandSafeId(string value, string name)
    {
        if (!SafeId.IsMatch(value))
        {
            throw new ArgumentException("Value is not a safe source identifier.", name);
        }
    }

    private static void DemandBlock(PdfBlock block)
    {
        if (string.IsNullOrWhiteSpace(block.NormalizedText)
            || block.BlockId.Length > 256
            || block.Anchor.WordIds.Count == 0
            || block.Anchor.WordIds.Distinct().Count() != block.Anchor.WordIds.Count)
        {
            throw new InvalidDataException("Selected PDF block cannot be exported as source evidence.");
        }
    }
}
