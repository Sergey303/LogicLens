using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

public static class DocxEvidenceSelector
{
    private static readonly JsonSerializerOptions JsonOptions =
        new(JsonSerializerDefaults.Web);

    public static RetainedOoxmlEvidence Select(
        DocxDocument document,
        string sourceId,
        IReadOnlyCollection<string> blockIds
    )
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(blockIds);
        var requested = DemandUniqueSelection(blockIds);
        var selected = document.Blocks
            .Where(block => requested.Remove(block.BlockId))
            .Select(block => new OoxmlSelectedFragment(
                block.BlockId,
                block.Kind,
                block.NormalizedText,
                block.ContentSha256,
                JsonSerializer.SerializeToElement(new
                {
                    format = "docx",
                    block.Anchor.SectionIndex,
                    block.Anchor.BodyOrder,
                    block.Anchor.ParagraphIndex,
                    block.Anchor.TableIndex,
                    block.Anchor.RowIndex,
                    block.Anchor.ColumnIndex,
                    kind = block.Kind,
                }, JsonOptions),
                Array.Empty<string>()
            ))
            .ToArray();
        DemandAllFound(requested, "DOCX block");
        return new RetainedOoxmlEvidence(
            sourceId,
            document.ArtifactSha256,
            document.Adapter,
            document.AdapterVersion,
            selected
        );
    }

    private static HashSet<string> DemandUniqueSelection(IReadOnlyCollection<string> blockIds)
    {
        if (blockIds.Count == 0)
        {
            throw new ArgumentException("At least one DOCX block is required.", nameof(blockIds));
        }
        var requested = new HashSet<string>(blockIds, StringComparer.Ordinal);
        if (requested.Count != blockIds.Count)
        {
            throw new ArgumentException("DOCX block IDs must be unique.", nameof(blockIds));
        }
        return requested;
    }

    private static void DemandAllFound(HashSet<string> remaining, string kind)
    {
        if (remaining.Count > 0)
        {
            throw new KeyNotFoundException($"Unknown {kind} IDs: {string.Join(", ", remaining)}");
        }
    }
}
