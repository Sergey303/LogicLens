using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class ProcessingJobLeaseContractTests
{
    public static void FirstLeaseOwnsAttemptAndBlocksSecondWorker()
    {
        var firstToken = Guid.NewGuid();
        var leased = ProcessingJobTestData.Lease(ProcessingJobTestData.Pending(), firstToken);
        var second = ProcessingJobStateMachine.TryLease(
            leased,
            ProcessingJobTestData.Now.AddMinutes(1),
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        );

        ProcessingJobTestData.Assert(leased.State == ProcessingJobState.Leased, "Job was not leased.");
        ProcessingJobTestData.Assert(leased.Attempt == 1, "First lease did not increment attempt.");
        ProcessingJobTestData.Assert(leased.LeaseToken == firstToken, "Lease token changed.");
        ProcessingJobTestData.Assert(second is null, "Active lease was stolen by another worker.");
    }

    public static void ExpiredLeaseCanBeReclaimed()
    {
        var first = ProcessingJobTestData.Lease(
            ProcessingJobTestData.Pending(),
            Guid.NewGuid(),
            duration: TimeSpan.FromMinutes(1)
        );
        var secondToken = Guid.NewGuid();
        var reclaimed = ProcessingJobStateMachine.TryLease(
            first,
            ProcessingJobTestData.Now.AddMinutes(2),
            TimeSpan.FromMinutes(5),
            secondToken
        );

        ProcessingJobTestData.Assert(reclaimed is not null, "Expired lease was not reclaimed.");
        ProcessingJobTestData.Assert(reclaimed!.Attempt == 2, "Reclaim did not increment attempt.");
        ProcessingJobTestData.Assert(reclaimed.LeaseToken == secondToken, "Reclaim kept stale token.");
    }

    public static async Task StaleOrExpiredLeaseCannotCompleteAsync()
    {
        var validToken = Guid.NewGuid();
        var leased = ProcessingJobTestData.Lease(ProcessingJobTestData.Pending(), validToken);

        await ProcessingJobTestData.ThrowsAsync<InvalidOperationException>(
            () => Task.Run(() => ProcessingJobStateMachine.Complete(
                leased,
                Guid.NewGuid(),
                ProcessingJobTestData.Now.AddMinutes(1)
            )),
            "Stale lease token completed a processing job."
        );
        await ProcessingJobTestData.ThrowsAsync<InvalidOperationException>(
            () => Task.Run(() => ProcessingJobStateMachine.Complete(
                leased,
                validToken,
                ProcessingJobTestData.Now.AddMinutes(6)
            )),
            "Expired lease completed a processing job."
        );
    }

    public static void ActiveLeaseCompletesAndTerminalCannotRelock()
    {
        var token = Guid.NewGuid();
        var leased = ProcessingJobTestData.Lease(ProcessingJobTestData.Pending(), token);
        var completed = ProcessingJobStateMachine.Complete(
            leased,
            token,
            ProcessingJobTestData.Now.AddMinutes(1)
        );
        var relock = ProcessingJobStateMachine.TryLease(
            completed,
            ProcessingJobTestData.Now.AddMinutes(2),
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        );

        ProcessingJobTestData.Assert(completed.State == ProcessingJobState.Succeeded, "Job not completed.");
        ProcessingJobTestData.Assert(completed.LeaseToken is null, "Completed job retained lease.");
        ProcessingJobTestData.Assert(relock is null, "Completed job became leasable again.");
    }
}
