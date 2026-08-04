using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlSourceProposalBridge
{
    private const int MaxFragmentChars = 7_000;
    private static readonly Regex SafeId = new(
        "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly Regex LowerSha256 = new(
        "^[0-9a-f]{64}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly Regex DomainHash = new(
        "^sha256:[0-9a-f]{64}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    public static byte[] ExportJsonLines(
        string proposalId,
        string snapshotHash,
        RetainedOoxmlEvidence evidence
    )
    {
        ArgumentNullException.ThrowIfNull(evidence);
        DemandSafeId(proposalId, nameof(proposalId));
        DemandSafeId(evidence.SourceId, nameof(evidence.SourceId));
        if (!DomainHash.IsMatch(snapshotHash))
        {
            throw new ArgumentException("Snapshot hash must use sha256:<lowercase hex>.", nameof(snapshotHash));
        }
        DemandEvidence(evidence);
        var output = new StringBuilder();
        var ordinal = 0;
        foreach (var fragment in evidence.Fragments)
        {
            DemandFragment(fragment);
            var chunks = Chunk(fragment.Text);
            for (var chunkIndex = 0; chunkIndex < chunks.Count; chunkIndex++)
            {
                ordinal++;
                var suffix = chunks.Count > 1 ? $":c{chunkIndex + 1:000}" : "";
                var row = new
                {
                    schemaVersion = "0.1",
                    fragmentId = $"{evidence.SourceId}#ooxml-{ordinal:000000}{suffix}",
                    proposalId,
                    sourceId = evidence.SourceId,
                    snapshotHash,
                    ordinal,
                    headingPath = fragment.HeadingPath,
                    lineStart = 1,
                    lineEnd = chunks[chunkIndex].Count(character => character == '\n') + 1,
                    blockIds = new[] { fragment.StableId },
                    sourceAnchor = fragment.SourceAnchor,
                    processor = new
                    {
                        name = evidence.AdapterName,
                        version = evidence.AdapterVersion,
                        artifactSha256 = $"sha256:{evidence.ArtifactSha256}",
                    },
                    text = chunks[chunkIndex],
                    textHash = $"sha256:{SourceFragmentTextHash(chunks[chunkIndex])}",
                };
                output.Append(JsonSerializer.Serialize(row, JsonOptions)).Append('\n');
            }
        }
        return Encoding.UTF8.GetBytes(output.ToString());
    }

    private static void DemandEvidence(RetainedOoxmlEvidence evidence)
    {
        if (evidence.Fragments.Count == 0
            || evidence.Fragments.Select(item => item.StableId).Distinct().Count()
                != evidence.Fragments.Count
            || !LowerSha256.IsMatch(evidence.ArtifactSha256)
            || string.IsNullOrWhiteSpace(evidence.AdapterName)
            || string.IsNullOrWhiteSpace(evidence.AdapterVersion))
        {
            throw new InvalidDataException("Retained OOXML evidence is invalid.");
        }
    }

    private static void DemandFragment(OoxmlSelectedFragment fragment)
    {
        if (string.IsNullOrWhiteSpace(fragment.StableId)
            || fragment.StableId.Length > 256
            || string.IsNullOrWhiteSpace(fragment.Text)
            || !LowerSha256.IsMatch(fragment.ContentSha256)
            || fragment.SourceAnchor.ValueKind != JsonValueKind.Object
            || fragment.HeadingPath.Any(item => string.IsNullOrWhiteSpace(item)))
        {
            throw new InvalidDataException("Selected OOXML fragment cannot be exported.");
        }
    }

    private static IReadOnlyList<string> Chunk(string text)
    {
        var chunks = new List<string>();
        for (var offset = 0; offset < text.Length; offset += MaxFragmentChars)
        {
            chunks.Add(text.Substring(offset, Math.Min(MaxFragmentChars, text.Length - offset)));
        }
        return chunks;
    }

    private static string SourceFragmentTextHash(string text)
    {
        var normalized = text.Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n')
            .TrimEnd() + "\n";
        return OoxmlHashing.Sha256(normalized);
    }

    private static void DemandSafeId(string value, string name)
    {
        if (!SafeId.IsMatch(value))
        {
            throw new ArgumentException("Value is not a safe source identifier.", name);
        }
    }
}
