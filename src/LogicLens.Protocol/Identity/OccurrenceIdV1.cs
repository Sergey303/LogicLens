using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;

namespace LogicLens.Protocol.Identity;

public enum OccurrenceDirection : byte
{
    Outgoing = 0x01,
    Incoming = 0x02
}

public sealed record OccurrenceStep(
    string FactId,
    OccurrenceDirection Direction);

public static class OccurrenceIdV1
{
    private static readonly byte[] Header =
        Encoding.ASCII.GetBytes("LogicLensOccurrence\0");

    public const byte EncodingVersion = 0x01;

    public static string Compute(
        string root,
        IReadOnlyList<OccurrenceStep> steps)
    {
        var bytes = Encode(root, steps);
        var hash = SHA256.HashData(bytes);
        return $"o:sha256:{Convert.ToHexString(hash).ToLowerInvariant()}";
    }

    public static byte[] Encode(
        string root,
        IReadOnlyList<OccurrenceStep> steps)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(root);
        ArgumentNullException.ThrowIfNull(steps);

        using var stream = new MemoryStream();
        stream.Write(Header);
        stream.WriteByte(EncodingVersion);
        WriteField(stream, root);

        foreach (var step in steps)
        {
            ArgumentNullException.ThrowIfNull(step);
            ArgumentException.ThrowIfNullOrWhiteSpace(step.FactId);
            WriteField(stream, step.FactId);
            stream.WriteByte((byte)step.Direction);
        }

        return stream.ToArray();
    }

    public static string EncodeHex(
        string root,
        IReadOnlyList<OccurrenceStep> steps) =>
        Convert.ToHexString(Encode(root, steps)).ToLowerInvariant();

    private static void WriteField(Stream stream, string value)
    {
        var bytes = Encoding.UTF8.GetBytes(value);
        Span<byte> length = stackalloc byte[sizeof(ulong)];
        BinaryPrimitives.WriteUInt64BigEndian(length, checked((ulong)bytes.Length));
        stream.Write(length);
        stream.Write(bytes);
    }
}
