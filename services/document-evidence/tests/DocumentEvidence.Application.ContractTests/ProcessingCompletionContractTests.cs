using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class ProcessingCompletionContractTests
{
    public static async Task LiveLeasePersistsCanonicalPayloadAsync()
    {
        var repository = new RecordingCompletionRepository(result: true);
        var service = new ProcessingCompletionService(repository);
        var expected = LeasedJob(DateTimeOffset.UtcNow);
        var completion = Completion(expected.LeaseUntil!.Value.AddSeconds(-1));

        await service.CompleteAsync(expected, completion);

        Assert(repository.Calls == 1, "A valid completion must reach the repository once.");
        Assert(repository.LastCompletion == completion, "Completion payload must be preserved.");
    }

    public static async Task ExpiredLeaseStopsBeforeRepositoryAsync()
    {
        var repository = new RecordingCompletionRepository(result: true);
        var service = new ProcessingCompletionService(repository);
        var expected = LeasedJob(DateTimeOffset.UtcNow.AddMinutes(-2));

        await AssertThrowsAsync<InvalidOperationException>(() =>
            service.CompleteAsync(expected, Completion(DateTimeOffset.UtcNow))
        );
        Assert(repository.Calls == 0, "Expired lease must stop before persistence.");
    }

    public static async Task LostCasFailsClosedAsync()
    {
        var repository = new RecordingCompletionRepository(result: false);
        var service = new ProcessingCompletionService(repository);
        var expected = LeasedJob(DateTimeOffset.UtcNow);

        await AssertThrowsAsync<InvalidOperationException>(() =>
            service.CompleteAsync(expected, Completion(expected.LeaseUntil!.Value.AddSeconds(-1)))
        );
        Assert(repository.Calls == 1, "CAS conflict must be observed exactly once.");
    }

    private static ProcessingJobSnapshot LeasedJob(DateTimeOffset now) => new(
        Guid.NewGuid(),
        ProcessingJobState.Leased,
        1,
        3,
        now,
        Guid.NewGuid(),
        now.AddMinutes(1),
        null
    );

    private static ProcessingCompletionPayload Completion(DateTimeOffset completedAt)
    {
        var revisionId = Guid.NewGuid();
        var hash = new string('a', 64);
        return new ProcessingCompletionPayload(
            revisionId,
            completedAt,
            new ProcessingArtifactManifest(
                "poppler-bbox",
                "24.02.0",
                hash,
                hash,
                hash,
                "{}",
                hash
            ),
            [new ProcessingFragmentWrite(Guid.NewGuid(), revisionId, 1, "paragraph", "{}", "Text", hash)]
        );
    }

    private static async Task AssertThrowsAsync<T>(Func<Task> action) where T : Exception
    {
        try
        {
            await action();
            throw new InvalidOperationException($"Expected {typeof(T).Name}.");
        }
        catch (T)
        {
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}

internal sealed class RecordingCompletionRepository : IProcessingCompletionRepository
{
    private readonly bool _result;

    public RecordingCompletionRepository(bool result)
    {
        _result = result;
    }

    public int Calls { get; private set; }
    public ProcessingCompletionPayload? LastCompletion { get; private set; }

    public Task<bool> TryCompleteAsync(
        ProcessingJobSnapshot expectedJob,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    )
    {
        Calls++;
        LastCompletion = completion;
        return Task.FromResult(_result);
    }
}
