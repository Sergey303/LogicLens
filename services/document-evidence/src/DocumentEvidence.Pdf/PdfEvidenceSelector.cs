namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public static class PdfEvidenceSelector
{
    public static RetainedPdfEvidence Select(
        PdfExtractionResult extraction,
        IReadOnlyCollection<string> blockIds
    )
    {
        ArgumentNullException.ThrowIfNull(extraction);
        ArgumentNullException.ThrowIfNull(blockIds);
        if (blockIds.Count == 0)
        {
            throw new ArgumentException("At least one selected block is required.", nameof(blockIds));
        }

        var requested = new HashSet<string>(blockIds, StringComparer.Ordinal);
        if (requested.Count != blockIds.Count)
        {
            throw new ArgumentException("Selected block IDs must be unique.", nameof(blockIds));
        }
        var selected = extraction.Document.Pages
            .SelectMany(page => page.Blocks)
            .Where(block => requested.Remove(block.BlockId))
            .OrderBy(block => block.Anchor.PageNumber)
            .ThenBy(block => block.ReadingOrder)
            .ToList();
        if (requested.Count > 0)
        {
            throw new KeyNotFoundException($"Unknown PDF block IDs: {string.Join(", ", requested)}");
        }
        return new RetainedPdfEvidence(
            extraction.Document.SourceId,
            extraction.Document.Artifact.Sha256,
            extraction.Manifest.Version,
            selected
        );
    }
}
