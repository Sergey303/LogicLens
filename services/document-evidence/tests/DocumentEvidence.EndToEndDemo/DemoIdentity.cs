using System.Security.Cryptography;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal static class DemoIdentity
{
    public static string Sha256(ReadOnlySpan<byte> content)
    {
        return Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant();
    }

    public static Guid GuidFrom(string value)
    {
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(value));
        var bytes = hash[..16];
        bytes[6] = (byte)((bytes[6] & 0x0f) | 0x50);
        bytes[8] = (byte)((bytes[8] & 0x3f) | 0x80);
        return new Guid(bytes);
    }
}
