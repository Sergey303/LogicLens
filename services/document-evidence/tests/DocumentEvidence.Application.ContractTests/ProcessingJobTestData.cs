using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class ProcessingJobTestData
{
    public static readonly DateTimeOffset Now = new(2026, 8, 4, 12, 0, 0, TimeSpan.Zero);

    public static ProcessingJobSnapshot Pending(
        int attempt = 0,
        int maxAttempts = 3,
        DateTimeOffset? availableAt = null
    )
    {
        return new ProcessingJobSnapshot(
            Guid.NewGuid(),
            ProcessingJobState.Pending,
            attempt,
            maxAttempts,
            availableAt ?? Now,
            null,
            null,
            null
        );
    }

    public static ProcessingJobSnapshot Lease(
        ProcessingJobSnapshot job,
        Guid token,
        DateTimeOffset? now = null,
        TimeSpan? duration = null
    )
    {
        return ProcessingJobStateMachine.TryLease(
            job,
            now ?? Now,
            duration ?? TimeSpan.FromMinutes(5),
            token
        ) ?? throw new InvalidOperationException("Expected processing job to be leasable.");
    }

    public static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    public static async Task ThrowsAsync<TException>(Func<Task> action, string message)
        where TException : Exception
    {
        try
        {
            await action();
        }
        catch (TException)
        {
            return;
        }
        throw new InvalidOperationException(message);
    }
}
