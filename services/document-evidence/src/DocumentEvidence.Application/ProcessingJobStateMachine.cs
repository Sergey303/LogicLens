using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public static class ProcessingJobStateMachine
{
    public static ProcessingJobSnapshot? TryLease(
        ProcessingJobSnapshot job,
        DateTimeOffset now,
        TimeSpan leaseDuration,
        Guid leaseToken
    )
    {
        Validate(job);
        if (leaseToken == Guid.Empty)
        {
            throw new ArgumentException("Lease token is required.", nameof(leaseToken));
        }
        if (leaseDuration <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(leaseDuration));
        }
        if (job.State is ProcessingJobState.Succeeded or ProcessingJobState.FailedTerminal)
        {
            return null;
        }
        if (job.State == ProcessingJobState.Leased && job.LeaseUntil > now)
        {
            return null;
        }
        if (job.State != ProcessingJobState.Leased && job.AvailableAt > now)
        {
            return null;
        }
        if (job.Attempt >= job.MaxAttempts)
        {
            return job with
            {
                State = ProcessingJobState.FailedTerminal,
                LeaseToken = null,
                LeaseUntil = null,
                LastError = job.LastError ?? "Maximum attempts reached before lease.",
            };
        }

        return job with
        {
            State = ProcessingJobState.Leased,
            Attempt = job.Attempt + 1,
            LeaseToken = leaseToken,
            LeaseUntil = now + leaseDuration,
        };
    }

    public static ProcessingJobSnapshot Complete(
        ProcessingJobSnapshot job,
        Guid leaseToken,
        DateTimeOffset now
    )
    {
        DemandActiveLease(job, leaseToken, now);
        return job with
        {
            State = ProcessingJobState.Succeeded,
            AvailableAt = now,
            LeaseToken = null,
            LeaseUntil = null,
            LastError = null,
        };
    }

    public static ProcessingJobSnapshot Fail(
        ProcessingJobSnapshot job,
        Guid leaseToken,
        DateTimeOffset now,
        string error,
        TimeSpan baseDelay,
        TimeSpan maxDelay
    )
    {
        DemandActiveLease(job, leaseToken, now);
        error = DemandError(error);
        ValidateDelays(baseDelay, maxDelay);

        if (job.Attempt >= job.MaxAttempts)
        {
            return job with
            {
                State = ProcessingJobState.FailedTerminal,
                AvailableAt = now,
                LeaseToken = null,
                LeaseUntil = null,
                LastError = error,
            };
        }

        return job with
        {
            State = ProcessingJobState.RetryScheduled,
            AvailableAt = now + ComputeBackoff(job.Attempt, baseDelay, maxDelay),
            LeaseToken = null,
            LeaseUntil = null,
            LastError = error,
        };
    }

    private static void DemandActiveLease(
        ProcessingJobSnapshot job,
        Guid leaseToken,
        DateTimeOffset now
    )
    {
        Validate(job);
        if (leaseToken == Guid.Empty || job.State != ProcessingJobState.Leased)
        {
            throw new InvalidOperationException("Processing job does not have an active lease.");
        }
        if (job.LeaseToken != leaseToken)
        {
            throw new InvalidOperationException("Processing job lease token is stale.");
        }
        if (job.LeaseUntil <= now)
        {
            throw new InvalidOperationException("Processing job lease has expired.");
        }
    }

    private static TimeSpan ComputeBackoff(
        int attempt,
        TimeSpan baseDelay,
        TimeSpan maxDelay
    )
    {
        var exponent = Math.Clamp(attempt - 1, 0, 30);
        var factor = 1L << exponent;
        var ticks = baseDelay.Ticks > maxDelay.Ticks / factor
            ? maxDelay.Ticks
            : Math.Min(baseDelay.Ticks * factor, maxDelay.Ticks);
        return TimeSpan.FromTicks(ticks);
    }

    private static void Validate(ProcessingJobSnapshot job)
    {
        ArgumentNullException.ThrowIfNull(job);
        if (job.JobId == Guid.Empty || job.MaxAttempts <= 0)
        {
            throw new InvalidDataException("Processing job identity and MaxAttempts are required.");
        }
        if (job.Attempt < 0 || job.Attempt > job.MaxAttempts)
        {
            throw new InvalidDataException("Processing job attempt is outside its valid range.");
        }
        var hasLease = job.LeaseToken is not null || job.LeaseUntil is not null;
        if ((job.State == ProcessingJobState.Leased) != hasLease
            || (job.State == ProcessingJobState.Leased
                && (job.LeaseToken is null || job.LeaseUntil is null)))
        {
            throw new InvalidDataException("Processing job lease fields do not match its state.");
        }
        if (job.State == ProcessingJobState.RetryScheduled && job.Attempt >= job.MaxAttempts)
        {
            throw new InvalidDataException("Exhausted processing job cannot remain retryable.");
        }
    }

    private static string DemandError(string error)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(error);
        error = error.Trim();
        return error.Length <= 2000 ? error : error[..2000];
    }

    private static void ValidateDelays(TimeSpan baseDelay, TimeSpan maxDelay)
    {
        if (baseDelay <= TimeSpan.Zero || maxDelay < baseDelay)
        {
            throw new ArgumentOutOfRangeException(nameof(baseDelay));
        }
    }
}
