using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class ProcessingJobCoordinator
{
    private const int MaxLeaseRaces = 8;
    private readonly IProcessingJobRepository _repository;

    public ProcessingJobCoordinator(IProcessingJobRepository repository)
    {
        _repository = repository;
    }

    public async Task<ProcessingJobSnapshot?> TryLeaseNextAsync(
        DateTimeOffset now,
        TimeSpan leaseDuration,
        Guid leaseToken,
        CancellationToken cancellationToken = default
    )
    {
        for (var race = 0; race < MaxLeaseRaces; race++)
        {
            var candidate = await _repository.FindNextAvailableAsync(now, cancellationToken);
            if (candidate is null)
            {
                return null;
            }

            var leased = ProcessingJobStateMachine.TryLease(
                candidate,
                now,
                leaseDuration,
                leaseToken
            );
            if (leased is not null
                && await _repository.CompareExchangeAsync(
                    candidate,
                    leased,
                    cancellationToken
                ))
            {
                return leased;
            }
        }

        throw new InvalidOperationException("Processing job lease contention exceeded its retry limit.");
    }

    public async Task<ProcessingJobSnapshot> CompleteAsync(
        ProcessingJobSnapshot leased,
        Guid leaseToken,
        DateTimeOffset now,
        CancellationToken cancellationToken = default
    )
    {
        var completed = ProcessingJobStateMachine.Complete(leased, leaseToken, now);
        await DemandCompareExchangeAsync(leased, completed, cancellationToken);
        return completed;
    }

    public async Task<ProcessingJobSnapshot> FailAsync(
        ProcessingJobSnapshot leased,
        Guid leaseToken,
        DateTimeOffset now,
        string error,
        TimeSpan baseDelay,
        TimeSpan maxDelay,
        CancellationToken cancellationToken = default
    )
    {
        var failed = ProcessingJobStateMachine.Fail(
            leased,
            leaseToken,
            now,
            error,
            baseDelay,
            maxDelay
        );
        await DemandCompareExchangeAsync(leased, failed, cancellationToken);
        return failed;
    }

    private async Task DemandCompareExchangeAsync(
        ProcessingJobSnapshot expected,
        ProcessingJobSnapshot replacement,
        CancellationToken cancellationToken
    )
    {
        if (!await _repository.CompareExchangeAsync(expected, replacement, cancellationToken))
        {
            throw new InvalidOperationException(
                "Processing job changed concurrently; stale worker transition was rejected."
            );
        }
    }
}
