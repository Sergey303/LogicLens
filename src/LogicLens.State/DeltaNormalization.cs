using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using LogicLens.Core.Identity;
using LogicLens.Core.Model;

namespace LogicLens.State;

internal sealed record NormalizedDelta(
    string RequestHash,
    IReadOnlyList<CanonicalFact> Add,
    IReadOnlyList<string> Delete);

internal static class DeltaNormalizer
{
    private static readonly byte[] Header =
        Encoding.ASCII.GetBytes("LogicLensDelta\0");

    public static NormalizedDelta Normalize(
        ApplyDeltaCommand command,
        RuntimeStateStoreOptions options)
    {
        ArgumentNullException.ThrowIfNull(command);
        ArgumentNullException.ThrowIfNull(options);

        var operationCount = checked(command.Add.Count + command.Delete.Count);
        if (operationCount > options.MaxOperationsPerCommand)
        {
            throw new ArgumentException(
                $"Command contains {operationCount} operations; the limit is " +
                $"{options.MaxOperationsPerCommand}.",
                nameof(command));
        }

        var addById = new SortedDictionary<string, CanonicalFact>(
            StringComparer.Ordinal);
        foreach (var operation in command.Add)
        {
            var fact = operation.ToCanonicalFact();
            if (addById.TryGetValue(fact.FactId, out var existing))
            {
                if (!SameFact(existing, fact))
                {
                    throw new InvalidOperationException(
                        $"FactId collision detected for '{fact.FactId}'.");
                }
                continue;
            }
            addById.Add(fact.FactId, fact);
        }

        var delete = command.Delete
            .Select(static operation => operation.FactId)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(static factId => factId, StringComparer.Ordinal)
            .ToArray();
        var add = addById.Values.ToArray();
        var requestHash = ComputeRequestHash(command, add, delete);
        return new NormalizedDelta(requestHash, add, delete);
    }

    private static string ComputeRequestHash(
        ApplyDeltaCommand command,
        IReadOnlyList<CanonicalFact> add,
        IReadOnlyList<string> delete)
    {
        using var stream = new MemoryStream();
        stream.Write(Header);
        stream.WriteByte(0x01);
        WriteInt64(stream, command.ExpectedRevision);
        WriteField(stream, command.Actor);
        WriteInt32(stream, add.Count);
        foreach (var fact in add)
        {
            var bytes = FactIdV1.Encode(
                fact.Subject,
                fact.Predicate,
                fact.Object);
            WriteBytes(stream, bytes);
        }
        WriteInt32(stream, delete.Count);
        foreach (var factId in delete)
        {
            WriteField(stream, factId);
        }

        var hash = SHA256.HashData(stream.ToArray());
        return "sha256:" + Convert.ToHexString(hash).ToLowerInvariant();
    }

    private static void WriteField(Stream stream, string value) =>
        WriteBytes(stream, Encoding.UTF8.GetBytes(value));

    private static void WriteBytes(Stream stream, ReadOnlySpan<byte> value)
    {
        Span<byte> length = stackalloc byte[sizeof(int)];
        BinaryPrimitives.WriteInt32BigEndian(length, value.Length);
        stream.Write(length);
        stream.Write(value);
    }

    private static void WriteInt32(Stream stream, int value)
    {
        Span<byte> bytes = stackalloc byte[sizeof(int)];
        BinaryPrimitives.WriteInt32BigEndian(bytes, value);
        stream.Write(bytes);
    }

    private static void WriteInt64(Stream stream, long value)
    {
        Span<byte> bytes = stackalloc byte[sizeof(long)];
        BinaryPrimitives.WriteInt64BigEndian(bytes, value);
        stream.Write(bytes);
    }

    private static bool SameFact(CanonicalFact left, CanonicalFact right) =>
        StringComparer.Ordinal.Equals(left.Subject, right.Subject)
        && StringComparer.Ordinal.Equals(left.Predicate, right.Predicate)
        && Equals(left.Object, right.Object);
}
