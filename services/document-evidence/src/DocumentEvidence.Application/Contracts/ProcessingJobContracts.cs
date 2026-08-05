namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

public enum ProcessingJobState
{
    Pending,
    Leased,
    RetryScheduled,
    Succeeded,
    FailedTerminal,
}

public sealed record ProcessingJobSnapshot(
    Guid JobId,
    ProcessingJobState State,
    int Attempt,
    int MaxAttempts,
    DateTimeOffset AvailableAt,
    Guid? LeaseToken,
    DateTimeOffset? LeaseUntil,
    string? LastError
);
