using System.Security.Cryptography;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlDeterministicIdentity
{
    public static Guid CreateGuid(string identity)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(identity);
        Span<byte> bytes = stackalloc byte[16];
        SHA256.HashData(Encoding.UTF8.GetBytes(identity)).AsSpan(0, 16).CopyTo(bytes);
        bytes[6] = (byte)((bytes[6] & 0x0f) | 0x50);
        bytes[8] = (byte)((bytes[8] & 0x3f) | 0x80);
        return new Guid(bytes);
    }
}
