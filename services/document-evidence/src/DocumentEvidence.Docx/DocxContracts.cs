using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

public sealed record DocxSourceAnchor(
    int SectionIndex,
    int BodyOrder,
    int? ParagraphIndex,
    int? TableIndex,
    int? RowIndex,
    int? ColumnIndex
);

public sealed record DocxBlock(
    string BlockId,
    string Kind,
    string Text,
    string NormalizedText,
    string ContentSha256,
    DocxSourceAnchor Anchor
);

public sealed record DocxDocument(
    string Adapter,
    string AdapterVersion,
    string ArtifactSha256,
    string PackageEntriesSha256,
    string IrSha256,
    OoxmlCoreProperties CoreProperties,
    IReadOnlyList<DocxBlock> Blocks
);
