using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;

namespace LogicLens.State;

internal static class RuntimeStateLogCodec
{
    private static readonly byte[] Magic = Encoding.ASCII.GetBytes("LLSTLOG1");
    private static readonly byte[] CommitMarker = Encoding.ASCII.GetBytes("LLCMIT01");
    private const byte FormatVersion = 0x01;
    private const int HeaderSize = 8 + 1 + sizeof(long);
    private const int ChecksumSize = 32;
    private const int CommitMarkerSize = 8;

    public static void Append(
        FileStream stream,
        RuntimeLogRecord record,
        RuntimeStateStoreOptions options)
    {
        ArgumentNullException.ThrowIfNull(stream);
        ArgumentNullException.ThrowIfNull(record);
        ArgumentNullException.ThrowIfNull(options);

        var payload = RuntimeLogRecordJson.Serialize(record);
        if (payload.Length > options.MaxRecordBytes)
        {
            throw new ArgumentException(
                $"Runtime log record is {payload.Length} bytes; the limit is " +
                $"{options.MaxRecordBytes} bytes.",
                nameof(record));
        }
        var checksum = SHA256.HashData(payload);
        Span<byte> header = stackalloc byte[HeaderSize];
        Magic.CopyTo(header);
        header[Magic.Length] = FormatVersion;
        BinaryPrimitives.WriteInt64BigEndian(
            header[(Magic.Length + 1)..],
            payload.Length);

        stream.Position = stream.Length;
        stream.Write(header);
        options.FaultInjector?.OnFaultPoint(RuntimeStateFaultPoint.AfterHeader);
        stream.Write(payload);
        options.FaultInjector?.OnFaultPoint(RuntimeStateFaultPoint.AfterPayload);
        stream.Write(checksum);
        options.FaultInjector?.OnFaultPoint(RuntimeStateFaultPoint.AfterChecksum);
        stream.Write(CommitMarker);
        stream.Flush(flushToDisk: true);
        options.FaultInjector?.OnFaultPoint(RuntimeStateFaultPoint.AfterDurableFlush);
    }

    public static IReadOnlyList<RuntimeLogRecord> ReadAndRepairTail(
        FileStream stream,
        RuntimeStateStoreOptions options)
    {
        ArgumentNullException.ThrowIfNull(stream);
        ArgumentNullException.ThrowIfNull(options);

        var records = new List<RuntimeLogRecord>();
        stream.Position = 0;
        long lastValidOffset = 0;
        var truncateTail = false;

        while (stream.Position < stream.Length)
        {
            var frameOffset = stream.Position;
            var remaining = stream.Length - frameOffset;
            if (remaining < HeaderSize)
            {
                truncateTail = true;
                break;
            }

            var header = ReadExactly(stream, HeaderSize);
            if (!header.AsSpan(0, Magic.Length).SequenceEqual(Magic))
            {
                throw Corruption(frameOffset, "frame magic is invalid");
            }
            if (header[Magic.Length] != FormatVersion)
            {
                throw Corruption(frameOffset, "frame version is unsupported");
            }
            var payloadLength = BinaryPrimitives.ReadInt64BigEndian(
                header.AsSpan(Magic.Length + 1, sizeof(long)));
            if (payloadLength < 0 || payloadLength > options.MaxRecordBytes)
            {
                throw Corruption(frameOffset, "payload length is invalid");
            }

            var requiredTail = checked(
                payloadLength + ChecksumSize + CommitMarkerSize);
            if (stream.Length - stream.Position < requiredTail)
            {
                truncateTail = true;
                break;
            }

            var payload = ReadExactly(stream, checked((int)payloadLength));
            var checksum = ReadExactly(stream, ChecksumSize);
            var marker = ReadExactly(stream, CommitMarkerSize);
            if (!marker.AsSpan().SequenceEqual(CommitMarker))
            {
                throw Corruption(frameOffset, "commit marker is invalid");
            }
            var actualChecksum = SHA256.HashData(payload);
            if (!actualChecksum.AsSpan().SequenceEqual(checksum))
            {
                throw Corruption(frameOffset, "committed payload checksum is invalid");
            }

            RuntimeLogRecord record;
            try
            {
                record = RuntimeLogRecordJson.Deserialize(payload);
            }
            catch (RuntimeStateCorruptionException exception)
            {
                throw new RuntimeStateCorruptionException(
                    $"Runtime log frame at offset {frameOffset} has invalid content.",
                    exception);
            }
            records.Add(record);
            lastValidOffset = stream.Position;
        }

        if (truncateTail)
        {
            stream.SetLength(lastValidOffset);
            stream.Flush(flushToDisk: true);
        }
        stream.Position = stream.Length;
        return records;
    }

    private static byte[] ReadExactly(Stream stream, int count)
    {
        var bytes = new byte[count];
        var offset = 0;
        while (offset < count)
        {
            var read = stream.Read(bytes, offset, count - offset);
            if (read == 0)
            {
                throw new EndOfStreamException(
                    $"Unexpected end of runtime log after {offset} of {count} bytes.");
            }
            offset += read;
        }
        return bytes;
    }

    private static RuntimeStateCorruptionException Corruption(
        long offset,
        string message) =>
        new($"Runtime log frame at offset {offset}: {message}.");
}
