namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal sealed record PdfRawPage(
    int PageNumber,
    double Width,
    double Height,
    IReadOnlyList<PdfRawBlock> Blocks
);

internal sealed record PdfRawBlock(
    int Ordinal,
    string Text,
    string NormalizedText,
    PdfBoundingBox BoundingBox,
    IReadOnlyList<string> WordIds
);
