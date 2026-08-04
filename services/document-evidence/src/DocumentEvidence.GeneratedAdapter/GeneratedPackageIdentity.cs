using System.Text.Json;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

public sealed record GeneratedPackageIdentity(
    string AppForgeCommit,
    string ModelId,
    string ProjectFileName,
    string SourceSpecSha256,
    string PackageManifestSha256,
    string GeneratedTreeSha256
)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public static GeneratedPackageIdentity Load(string receiptPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(receiptPath);
        using var stream = File.OpenRead(receiptPath);
        var receipt = JsonSerializer.Deserialize<GenerationReceipt>(stream, JsonOptions)
            ?? throw InvalidReceipt("Receipt JSON is empty.");

        if (receipt.Kind != "logiclens-appforge-generation-receipt" || receipt.Version != 2)
        {
            throw InvalidReceipt("Receipt kind or version is unsupported.");
        }
        if (string.IsNullOrWhiteSpace(receipt.ModelId)
            || string.IsNullOrWhiteSpace(receipt.ProjectFileName))
        {
            throw InvalidReceipt("Generated model identity is incomplete.");
        }

        return new GeneratedPackageIdentity(
            DemandSha256(receipt.AppForgeCommit, nameof(receipt.AppForgeCommit)),
            receipt.ModelId,
            receipt.ProjectFileName,
            DemandSha256(receipt.SourceSpecSha256, nameof(receipt.SourceSpecSha256)),
            DemandSha256(receipt.PackageManifestSha256, nameof(receipt.PackageManifestSha256)),
            DemandSha256(
                receipt.GeneratedTreeSha256BeforeReceipt,
                nameof(receipt.GeneratedTreeSha256BeforeReceipt)
            )
        );
    }

    private static string DemandSha256(string? value, string field)
    {
        if (value is null || value.Length != 64 || value.Any(character => !Uri.IsHexDigit(character)))
        {
            throw InvalidReceipt($"Receipt field '{field}' must be a SHA-256 hex value.");
        }
        return value.ToLowerInvariant();
    }

    private static InvalidDataException InvalidReceipt(string message)
    {
        return new InvalidDataException($"Invalid AppForge generation receipt: {message}");
    }

    private sealed class GenerationReceipt
    {
        public string Kind { get; init; } = string.Empty;

        public int Version { get; init; }

        public string? AppForgeCommit { get; init; }

        public string ModelId { get; init; } = string.Empty;

        public string ProjectFileName { get; init; } = string.Empty;

        public string? SourceSpecSha256 { get; init; }

        public string? PackageManifestSha256 { get; init; }

        public string? GeneratedTreeSha256BeforeReceipt { get; init; }
    }
}
