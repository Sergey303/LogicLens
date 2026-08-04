namespace LogicLens.DocumentEvidence.Generated;

public sealed class AppForgeSeedHistory
{
    public Guid Id { get; set; }
    public string ModelId { get; set; } = string.Empty;
    public string ModelVersion { get; set; } = string.Empty;
    public string SeedSetName { get; set; } = string.Empty;
    public string TableName { get; set; } = string.Empty;
    public string SourceMdHash { get; set; } = string.Empty;
    public string SeedHash { get; set; } = string.Empty;
    public DateTime AppliedAt { get; set; }
}
