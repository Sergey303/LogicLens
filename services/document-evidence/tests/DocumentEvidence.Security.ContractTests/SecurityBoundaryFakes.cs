using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal sealed class RecordingAuthorization : IUploadAuthorizationPolicy
{
    private readonly bool _deny;
    private readonly List<string> _events;

    public RecordingAuthorization(List<string> events, bool deny = false)
    {
        _events = events;
        _deny = deny;
    }

    public ValueTask DemandWorkspaceUploadAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("authorization");
        if (_deny)
        {
            throw new UnauthorizedAccessException();
        }
        return ValueTask.CompletedTask;
    }
}

internal sealed class RecordingQuotaGate : IUploadQuotaGate
{
    private readonly bool _denyBytes;
    private readonly bool _denyRequest;
    private readonly List<string> _events;

    public RecordingQuotaGate(
        List<string> events,
        bool denyRequest = false,
        bool denyBytes = false
    )
    {
        _events = events;
        _denyRequest = denyRequest;
        _denyBytes = denyBytes;
    }

    public ValueTask DemandRequestAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("quota:request");
        if (_denyRequest)
        {
            throw new UploadQuotaExceededException("hourly-request-limit");
        }
        return ValueTask.CompletedTask;
    }

    public ValueTask DemandBytesAsync(
        Guid workspaceId,
        long sizeBytes,
        CancellationToken cancellationToken
    )
    {
        _events.Add($"quota:bytes:{sizeBytes}");
        if (_denyBytes)
        {
            throw new UploadQuotaExceededException("daily-byte-limit");
        }
        return ValueTask.CompletedTask;
    }
}

internal sealed class RecordingAuditSink : IUploadAuditSink
{
    public List<UploadAuditRecord> Records { get; } = [];

    public ValueTask RecordAsync(
        UploadAuditRecord record,
        CancellationToken cancellationToken
    )
    {
        Records.Add(record);
        return ValueTask.CompletedTask;
    }
}

internal sealed class ReadTrackingStream : Stream
{
    private readonly MemoryStream _inner;

    public ReadTrackingStream(byte[] content)
    {
        _inner = new MemoryStream(content, writable: false);
    }

    public int ReadCalls { get; private set; }
    public override bool CanRead => true;
    public override bool CanSeek => false;
    public override bool CanWrite => false;
    public override long Length => _inner.Length;
    public override long Position { get => _inner.Position; set => throw new NotSupportedException(); }

    public override int Read(byte[] buffer, int offset, int count)
    {
        ReadCalls++;
        return _inner.Read(buffer, offset, count);
    }

    public override ValueTask<int> ReadAsync(
        Memory<byte> buffer,
        CancellationToken cancellationToken = default
    )
    {
        ReadCalls++;
        return _inner.ReadAsync(buffer, cancellationToken);
    }

    public override void Flush() => throw new NotSupportedException();
    public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
    public override void SetLength(long value) => throw new NotSupportedException();
    public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _inner.Dispose();
        }
        base.Dispose(disposing);
    }
}
