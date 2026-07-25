namespace LogicLens.OntologyCompiler;

internal enum OntologyTermKind
{
    Class,
    DatatypeProperty,
    ObjectProperty,
    EnumerationType
}

internal enum OntologyLabelDirection
{
    Forward,
    Inverse
}

internal sealed record OntologyLabel(
    OntologyLabelDirection Direction,
    string Language,
    string Text);

internal sealed record OntologyTerm(
    string Id,
    OntologyTermKind Kind,
    string? Priority,
    IReadOnlyList<OntologyLabel> Labels);

internal sealed record OntologySnapshot(
    string SourcePath,
    string SourceDbId,
    IReadOnlyList<OntologyTerm> Terms)
{
    public int LabelCount => Terms.Sum(static term => term.Labels.Count);
}
