using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class RecordingImmutableObjectStore : IImmutableObjectStore
{
    public RecordingImmutableObjectStore(StoredObjectReference result)
    {
        Result = result;
    }

    public int PutCount { get; private set; }

    public StoredObjectReference Result { get; }

    public Task<StoredObjectReference> PutAsync(
        Stream content,
        CancellationToken cancellationToken
    )
    {
        PutCount++;
        return Task.FromResult(Result);
    }

    public Task<Stream> OpenReadAsync(string sha256, CancellationToken cancellationToken)
    {
        throw new NotSupportedException();
    }
}

internal sealed class RecordingLifecycleRepository : IDocumentLifecycleRepository
{
    public UploadCompletionResult? Existing { get; init; }

    public Func<UploadCompletionCommit, UploadCompletionResult>? CommitResult { get; init; }

    public int CommitCount { get; private set; }

    public UploadCompletionCommit? LastCommit { get; private set; }

    public Task<UploadCompletionResult?> FindUploadCompletionAsync(
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    )
    {
        return Task.FromResult(Existing);
    }

    public Task<UploadCompletionResult> CommitUploadAndEnqueueProcessingAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        CommitCount++;
        LastCommit = commit;
        var result = CommitResult?.Invoke(commit)
            ?? UploadTestData.Result(commit, replayed: false);
        return Task.FromResult(result);
    }
}

internal static class UploadTestData
{
    public static UploadCompletionResult Result(
        UploadCompletionCommit commit,
        bool replayed
    )
    {
        return new UploadCompletionResult(
            commit.WorkspaceId,
            commit.DocumentId,
            Guid.NewGuid(),
            1,
            Guid.NewGuid(),
            Guid.NewGuid(),
            commit.Manifest.Sha256,
            replayed
        );
    }
}
