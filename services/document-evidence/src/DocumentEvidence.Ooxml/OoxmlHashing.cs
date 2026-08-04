using System.Security.Cryptography;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlHashing
{
    public static string Sha256(ReadOnlySpan<byte> content) =>
        Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant();

    public static string Sha256(string content) =>
        Sha256(Encoding.UTF8.GetBytes(content));

    internal static string EntriesSha256(IEnumerable<OoxmlPart> parts)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var part in parts.OrderBy(item => item.Name, StringComparer.Ordinal))
        {
            Append(hash, part.Name);
            Append(hash, part.Content.LongLength.ToString(System.Globalization.CultureInfo.InvariantCulture));
            Append(hash, part.ContentSha256);
        }
        return Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant();
    }

    private static void Append(IncrementalHash hash, string value)
    {
        hash.AppendData(Encoding.UTF8.GetBytes(value));
        hash.AppendData([0]);
    }
}
