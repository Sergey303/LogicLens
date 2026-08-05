using System.Security.Cryptography;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal sealed class RecordingObjectStore : IImmutableObjectStore
{
    private readonly List<string> _events;

    public RecordingObjectStore(List<string> events)
    {
        _events = events;
    }

    public int Writes { get; private set; }

    public async Task<StoredObjectReference> PutAsync(
        Stream content,
        CancellationToken cancellationToken
    )
    {
        _events.Add("storage");
        Writes++;
        using var output = new MemoryStream();
        await content.CopyToAsync(output, cancellationToken);
        var bytes = output.ToArray();
        var hash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        return new StoredObjectReference(hash, bytes.LongLength, $"objects/{hash}", true);
    }

    public Task<Stream> OpenReadAsync(
        string sha256,
        CancellationToken cancellationToken
    ) => throw new NotSupportedException();
}

internal sealed class RecordingLifecycleRepository : IDocumentLifecycleRepository
{
    private readonly List<string> _events;

    public RecordingLifecycleRepository(List<string> events)
    {
        _events = events;
    }

    public UploadCompletionResult? Existing { get; init; }
    public UploadCompletionCommit? Commit { get; private set; }

    public Task<UploadCompletionResult?> FindUploadCompletionAsync(
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    )
    {
        _events.Add("repository:find");
        return Task.FromResult(Existing);
    }

    public Task<UploadCompletionResult> CommitUploadAndEnqueueProcessingAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        _events.Add("repository:commit");
        Commit = commit;
        return Task.FromResult(new UploadCompletionResult(
            commit.WorkspaceId,
            commit.DocumentId,
            Guid.Parse("11111111-1111-1111-1111-111111111111"),
            1,
            Guid.Parse("22222222-2222-2222-2222-222222222222"),
            Guid.Parse("33333333-3333-3333-3333-333333333333"),
            commit.Manifest.Sha256,
            false
        ));
    }
}
