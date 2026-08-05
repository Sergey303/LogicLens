using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class ProcessingJobFailureContractTests
{
    public static void FailureSchedulesDeterministicBackoff()
    {
        var firstToken = Guid.NewGuid();
        var firstLease = ProcessingJobTestData.Lease(ProcessingJobTestData.Pending(), firstToken);
        var firstFailure = ProcessingJobStateMachine.Fail(
            firstLease,
            firstToken,
            ProcessingJobTestData.Now.AddSeconds(10),
            " transient parser failure ",
            TimeSpan.FromSeconds(30),
            TimeSpan.FromMinutes(10)
        );
        var secondToken = Guid.NewGuid();
        var secondLease = ProcessingJobTestData.Lease(
            firstFailure,
            secondToken,
            now: firstFailure.AvailableAt
        );
        var secondFailureAt = firstFailure.AvailableAt.AddSeconds(10);
        var secondFailure = ProcessingJobStateMachine.Fail(
            secondLease,
            secondToken,
            secondFailureAt,
            "still failing",
            TimeSpan.FromSeconds(30),
            TimeSpan.FromMinutes(10)
        );

        ProcessingJobTestData.Assert(
            firstFailure.AvailableAt == ProcessingJobTestData.Now.AddSeconds(40),
            "First retry delay was not base delay."
        );
        ProcessingJobTestData.Assert(firstFailure.LastError == "transient parser failure", "Error not trimmed.");
        ProcessingJobTestData.Assert(
            secondFailure.AvailableAt == secondFailureAt.AddMinutes(1),
            "Second retry delay was not doubled."
        );
    }

    public static void RetryCannotLeaseBeforeAvailableAt()
    {
        var token = Guid.NewGuid();
        var lease = ProcessingJobTestData.Lease(ProcessingJobTestData.Pending(), token);
        var retry = ProcessingJobStateMachine.Fail(
            lease,
            token,
            ProcessingJobTestData.Now,
            "retry later",
            TimeSpan.FromMinutes(1),
            TimeSpan.FromMinutes(10)
        );
        var early = ProcessingJobStateMachine.TryLease(
            retry,
            ProcessingJobTestData.Now.AddSeconds(59),
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        );

        ProcessingJobTestData.Assert(early is null, "Retry leased before AvailableAt.");
    }

    public static void FinalAttemptBecomesTerminal()
    {
        var pending = ProcessingJobTestData.Pending(attempt: 2, maxAttempts: 3);
        var token = Guid.NewGuid();
        var finalLease = ProcessingJobTestData.Lease(pending, token);
        var terminal = ProcessingJobStateMachine.Fail(
            finalLease,
            token,
            ProcessingJobTestData.Now.AddSeconds(5),
            "permanent parser failure",
            TimeSpan.FromSeconds(30),
            TimeSpan.FromMinutes(10)
        );
        var relock = ProcessingJobStateMachine.TryLease(
            terminal,
            ProcessingJobTestData.Now.AddHours(1),
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        );

        ProcessingJobTestData.Assert(
            terminal.State == ProcessingJobState.FailedTerminal,
            "Exhausted job remained retryable."
        );
        ProcessingJobTestData.Assert(terminal.LeaseToken is null, "Terminal job retained lease.");
        ProcessingJobTestData.Assert(relock is null, "Terminal job became leasable again.");
    }
}
