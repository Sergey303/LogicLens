using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using LogicLens.Core.Model;

namespace LogicLens.Core.Identity;

public static class FactIdV1
{
    private static readonly byte[] Header = Encoding.ASCII.GetBytes("LogicLensFact\0");

    public const byte EncodingVersion = 0x01;

    public static string Compute(
        string subject,
        string predicate,
        FactObject @object)
    {
        var canonicalBytes = Encode(subject, predicate, @object);
        var hash = SHA256.HashData(canonicalBytes);
        return $"f:sha256:{Convert.ToHexString(hash).ToLowerInvariant()}";
    }

    public static byte[] Encode(
        string subject,
        string predicate,
        FactObject @object)
    {
        subject = Guard.Required(subject, nameof(subject));
        predicate = Guard.Required(predicate, nameof(predicate));
        ArgumentNullException.ThrowIfNull(@object);

        using var stream = new MemoryStream();
        stream.Write(Header);
        stream.WriteByte(EncodingVersion);
        WriteField(stream, subject);
        WriteField(stream, predicate);

        switch (@object)
        {
            case IriObject iri:
                stream.WriteByte(0x01);
                WriteField(stream, iri.Value);
                break;

            case LiteralObject { Kind: LiteralKind.Plain } literal:
                stream.WriteByte(0x02);
                WriteField(stream, literal.Lexical);
                break;

            case LiteralObject { Kind: LiteralKind.Language } literal:
                stream.WriteByte(0x03);
                WriteField(
                    stream,
                    literal.Language
                    ?? throw new InvalidOperationException("Language literal has no language tag."));
                WriteField(stream, literal.Lexical);
                break;

            case LiteralObject { Kind: LiteralKind.Datatype } literal:
                stream.WriteByte(0x04);
                WriteField(
                    stream,
                    literal.Datatype
                    ?? throw new InvalidOperationException("Datatype literal has no datatype IRI."));
                WriteField(stream, literal.Lexical);
                break;

            default:
                throw new ArgumentOutOfRangeException(
                    nameof(@object),
                    @object,
                    "Unsupported canonical fact object.");
        }

        return stream.ToArray();
    }

    public static string EncodeHex(
        string subject,
        string predicate,
        FactObject @object) =>
        Convert.ToHexString(Encode(subject, predicate, @object)).ToLowerInvariant();

    private static void WriteField(Stream stream, string value)
    {
        var bytes = Encoding.UTF8.GetBytes(value);
        Span<byte> length = stackalloc byte[sizeof(ulong)];
        BinaryPrimitives.WriteUInt64BigEndian(length, checked((ulong)bytes.Length));
        stream.Write(length);
        stream.Write(bytes);
    }
}
