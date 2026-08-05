namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public sealed record UploadQuotaOptions(
    int MaxRequestsPerHour = 20,
    long MaxBytesPerDay = 536_870_912
);

public sealed class InMemoryUploadQuotaGate : IUploadQuotaGate
{
    private readonly Dictionary<RequestKey, int> _requests = [];
    private readonly Dictionary<ByteKey, long> _bytes = [];
    private readonly object _sync = new();
    private readonly TimeProvider _timeProvider;
    private readonly UploadQuotaOptions _options;

    public InMemoryUploadQuotaGate(
        UploadQuotaOptions? options = null,
        TimeProvider? timeProvider = null
    )
    {
        _options = options ?? new UploadQuotaOptions();
        _timeProvider = timeProvider ?? TimeProvider.System;
        if (_options.MaxRequestsPerHour < 1 || _options.MaxBytesPerDay < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(options));
        }
    }

    public ValueTask DemandRequestAsync(
        Guid actorId,
        Guid workspaceId,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        var now = _timeProvider.GetUtcNow();
        var key = new RequestKey(actorId, workspaceId, HourBucket(now));
        lock (_sync)
        {
            var current = _requests.GetValueOrDefault(key);
            if (current >= _options.MaxRequestsPerHour)
            {
                throw new UploadQuotaExceededException("hourly-request-limit");
            }
            _requests[key] = checked(current + 1);
        }
        return ValueTask.CompletedTask;
    }

    public ValueTask DemandBytesAsync(
        Guid workspaceId,
        long sizeBytes,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (sizeBytes < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(sizeBytes));
        }
        var now = _timeProvider.GetUtcNow();
        var key = new ByteKey(workspaceId, DateOnly.FromDateTime(now.UtcDateTime));
        lock (_sync)
        {
            var current = _bytes.GetValueOrDefault(key);
            if (sizeBytes > _options.MaxBytesPerDay - current)
            {
                throw new UploadQuotaExceededException("daily-byte-limit");
            }
            _bytes[key] = checked(current + sizeBytes);
        }
        return ValueTask.CompletedTask;
    }

    private static DateTimeOffset HourBucket(DateTimeOffset value)
    {
        return new DateTimeOffset(
            value.Year,
            value.Month,
            value.Day,
            value.Hour,
            0,
            0,
            TimeSpan.Zero
        );
    }

    private readonly record struct RequestKey(
        Guid ActorId,
        Guid WorkspaceId,
        DateTimeOffset Hour
    );

    private readonly record struct ByteKey(Guid WorkspaceId, DateOnly Day);
}
