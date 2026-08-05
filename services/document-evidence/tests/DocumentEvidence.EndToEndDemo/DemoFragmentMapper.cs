using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal static class DemoFragmentMapper
{
    public static IReadOnlyList<DocumentFragmentDto> Map(
        PdfExtractionResult extraction,
        Guid revisionId
    )
    {
        return extraction.Document.Pages
            .SelectMany(page => page.Blocks)
            .OrderBy(block => block.Anchor.PageNumber)
            .ThenBy(block => block.ReadingOrder)
            .Select((block, index) => MapBlock(extraction, revisionId, block, index + 1))
            .ToArray();
    }

    private static DocumentFragmentDto MapBlock(
        PdfExtractionResult extraction,
        Guid revisionId,
        PdfBlock block,
        int sequence
    )
    {
        var anchor = JsonSerializer.SerializeToElement(new
        {
            sourceId = extraction.Document.SourceId,
            artifactSha256 = extraction.Document.Artifact.Sha256,
            parserVersion = extraction.Manifest.Version,
            blockId = block.BlockId,
            readingOrder = block.ReadingOrder,
            pageNumber = block.Anchor.PageNumber,
            blockOrdinal = block.Anchor.BlockOrdinal,
            boundingBox = new
            {
                block.Anchor.BoundingBox.XMin,
                block.Anchor.BoundingBox.YMin,
                block.Anchor.BoundingBox.XMax,
                block.Anchor.BoundingBox.YMax,
            },
            wordIds = block.Anchor.WordIds,
        });
        return new DocumentFragmentDto(
            DemoIdentity.GuidFrom($"fragment:{extraction.Document.Artifact.Sha256}:{block.BlockId}"),
            revisionId,
            sequence,
            block.Kind,
            new FragmentAnchorDto("pdf-block", anchor),
            block.NormalizedText,
            block.ContentSha256
        );
    }
}
