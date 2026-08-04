namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

public sealed record PostgresLifecycleOptions(
    int MaxAttempts = 5,
    string ProcessingKind = "ExtractFragments"
)
{
    public void Validate()
    {
        if (MaxAttempts <= 0 || MaxAttempts > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(MaxAttempts));
        }
        ArgumentException.ThrowIfNullOrWhiteSpace(ProcessingKind);
        if (ProcessingKind.Length > 80 || ProcessingKind != ProcessingKind.Trim())
        {
            throw new ArgumentException(
                "Processing kind must be trimmed and at most 80 characters.",
                nameof(ProcessingKind)
            );
        }
    }
}
