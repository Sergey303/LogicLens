using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

public sealed record XlsxCellAnchor(
    int SheetIndex,
    string SheetName,
    int RowIndex,
    int ColumnIndex,
    string CellReference
);

public sealed record XlsxCell(
    string CellId,
    string ValueKind,
    string? Formula,
    string? RawValue,
    string? CachedValue,
    string? DisplayValue,
    string ContentSha256,
    XlsxCellAnchor Anchor
);

public sealed record XlsxSheet(
    int SheetIndex,
    string Name,
    string PartName,
    IReadOnlyList<XlsxCell> Cells
);

public sealed record XlsxWorkbook(
    string Adapter,
    string AdapterVersion,
    string ArtifactSha256,
    string PackageEntriesSha256,
    string IrSha256,
    OoxmlCoreProperties CoreProperties,
    IReadOnlyList<XlsxSheet> Sheets
);
