namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public sealed record PdfExtractionRequest(
    string SourceId,
    string SourceUri,
    long MaxBytes,
    string? ExpectedSha256 = null
);

public sealed record PdfExtractionResult(
    PdfDocumentIr Document,
    PdfParserManifest Manifest
);

public sealed record PdfDocumentIr(
    string ContractVersion,
    string SourceId,
    PdfArtifact Artifact,
    IReadOnlyList<PdfPage> Pages,
    string IrSha256
);

public sealed record PdfArtifact(
    string Sha256,
    long SizeBytes,
    string MediaType,
    string SourceUri
);

public sealed record PdfPage(
    int PageNumber,
    double Width,
    double Height,
    string Unit,
    IReadOnlyList<PdfBlock> Blocks
);

public sealed record PdfBlock(
    string BlockId,
    int ReadingOrder,
    string Kind,
    string Text,
    string NormalizedText,
    string ContentSha256,
    PdfSourceAnchor Anchor
);

public sealed record PdfSourceAnchor(
    int PageNumber,
    int BlockOrdinal,
    PdfBoundingBox BoundingBox,
    IReadOnlyList<string> WordIds
);

public sealed record PdfBoundingBox(
    double XMin,
    double YMin,
    double XMax,
    double YMax
);

public sealed record PdfParserManifest(
    string Adapter,
    string Version,
    string ConfigurationSha256,
    string ArtifactSha256,
    string IrSha256
);

public sealed record RetainedPdfEvidence(
    string SourceId,
    string ArtifactSha256,
    string ParserVersion,
    IReadOnlyList<PdfBlock> Blocks
);
