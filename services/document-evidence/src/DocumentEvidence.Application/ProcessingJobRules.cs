using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

internal static class ProcessingJobRules
{
    public static void Validate(ProcessingJobSnapshot job)
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

        var hasToken = job.LeaseToken is not null;
        var hasUntil = job.LeaseUntil is not null;
        if (hasToken != hasUntil || (job.State == ProcessingJobState.Leased) != hasToken)
        {
            throw new InvalidDataException("Processing job lease fields do not match its state.");
        }
        if (job.State == ProcessingJobState.RetryScheduled && job.Attempt >= job.MaxAttempts)
        {
            throw new InvalidDataException("Exhausted processing job cannot remain retryable.");
        }
    }

    public static void DemandActiveLease(
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

    public static string DemandError(string error)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(error);
        error = error.Trim();
        return error.Length <= 2000 ? error : error[..2000];
    }

    public static TimeSpan ComputeBackoff(
        int attempt,
        TimeSpan baseDelay,
        TimeSpan maxDelay
    )
    {
        if (baseDelay <= TimeSpan.Zero || maxDelay < baseDelay)
        {
            throw new ArgumentOutOfRangeException(nameof(baseDelay));
        }

        var exponent = Math.Clamp(attempt - 1, 0, 30);
        var factor = 1L << exponent;
        var ticks = baseDelay.Ticks > maxDelay.Ticks / factor
            ? maxDelay.Ticks
            : Math.Min(baseDelay.Ticks * factor, maxDelay.Ticks);
        return TimeSpan.FromTicks(ticks);
    }
}
