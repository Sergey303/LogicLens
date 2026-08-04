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
        ProcessingJobRules.Validate(job);
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
        ProcessingJobRules.DemandActiveLease(job, leaseToken, now);
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
        ProcessingJobRules.DemandActiveLease(job, leaseToken, now);
        error = ProcessingJobRules.DemandError(error);
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

        var backoff = ProcessingJobRules.ComputeBackoff(job.Attempt, baseDelay, maxDelay);
        return job with
        {
            State = ProcessingJobState.RetryScheduled,
            AvailableAt = now + backoff,
            LeaseToken = null,
            LeaseUntil = null,
            LastError = error,
        };
    }
}
