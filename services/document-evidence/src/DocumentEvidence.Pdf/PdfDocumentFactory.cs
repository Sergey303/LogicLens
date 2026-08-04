namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal static class PdfDocumentFactory
{
    public static PdfDocumentIr Create(
        PdfExtractionRequest request,
        PdfValidatedInput input,
        PdfInfo info,
        IReadOnlyList<PdfRawPage> rawPages
    )
    {
        if (rawPages.Count != info.PageCount)
        {
            throw new InvalidDataException(
                $"Poppler page count mismatch: pdfinfo={info.PageCount}, bbox={rawPages.Count}."
            );
        }
        if (!rawPages.Any(page => page.Blocks.Count > 0))
        {
            throw new InvalidDataException(
                "PDF has no usable native text; a separate OCR adapter is required."
            );
        }

        var pages = rawPages.Select(page => CreatePage(request.SourceId, page)).ToList();
        var artifact = new PdfArtifact(
            input.Sha256,
            input.Bytes.LongLength,
            "application/pdf",
            request.SourceUri
        );
        var payload = new
        {
            contractVersion = "1.0",
            sourceId = request.SourceId,
            artifact,
            pages,
        };
        return new PdfDocumentIr(
            "1.0",
            request.SourceId,
            artifact,
            pages,
            PdfHashing.CanonicalSha256(payload)
        );
    }

    private static PdfPage CreatePage(string sourceId, PdfRawPage rawPage)
    {
        var blocks = rawPage.Blocks.Select(block => CreateBlock(sourceId, rawPage.PageNumber, block)).ToList();
        return new PdfPage(
            rawPage.PageNumber,
            rawPage.Width,
            rawPage.Height,
            "point",
            blocks
        );
    }

    private static PdfBlock CreateBlock(string sourceId, int pageNumber, PdfRawBlock rawBlock)
    {
        var contentSha256 = PdfHashing.Sha256(rawBlock.NormalizedText);
        var blockId = $"{sourceId}:p{pageNumber:0000}:b{rawBlock.Ordinal:0000}:{contentSha256[..12]}";
        return new PdfBlock(
            blockId,
            rawBlock.Ordinal,
            Classify(rawBlock.NormalizedText),
            rawBlock.Text,
            rawBlock.NormalizedText,
            contentSha256,
            new PdfSourceAnchor(
                pageNumber,
                rawBlock.Ordinal,
                rawBlock.BoundingBox,
                rawBlock.WordIds
            )
        );
    }

    private static string Classify(string text)
    {
        var firstLine = text.Split('\n')[0].Trim();
        if (firstLine.StartsWith("- ", StringComparison.Ordinal) ||
            firstLine.StartsWith("•", StringComparison.Ordinal) ||
            firstLine.StartsWith("* ", StringComparison.Ordinal))
        {
            return "list";
        }
        if (firstLine.Length <= 120 &&
            !firstLine.EndsWith('.') &&
            !firstLine.EndsWith(';') &&
            text.Count(character => character == '\n') <= 1)
        {
            return "heading";
        }
        return "paragraph";
    }
}
