using System.Collections.Concurrent;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoLifecycleRepository : IDocumentLifecycleRepository
{
    private readonly ConcurrentDictionary<(Guid WorkspaceId, string Key), UploadCompletionResult>
        _completions = new();
    private readonly ConcurrentDictionary<Guid, UploadCompletionCommit> _commits = new();

    public Task<UploadCompletionResult?> FindUploadCompletionAsync(
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        _completions.TryGetValue((workspaceId, idempotencyKey), out var result);
        return Task.FromResult(result);
    }

    public Task<UploadCompletionResult> CommitUploadAndEnqueueProcessingAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        var key = (commit.WorkspaceId, commit.IdempotencyKey);
        var result = _completions.GetOrAdd(key, _ => CreateResult(commit));
        _commits.TryAdd(result.RevisionId, commit);
        return Task.FromResult(result);
    }

    public UploadCompletionCommit GetCommit(Guid revisionId)
    {
        return _commits.TryGetValue(revisionId, out var commit)
            ? commit
            : throw new KeyNotFoundException($"Unknown demo revision: {revisionId:D}");
    }

    private static UploadCompletionResult CreateResult(UploadCompletionCommit commit)
    {
        return new UploadCompletionResult(
            commit.WorkspaceId,
            commit.DocumentId,
            DemoIdentity.GuidFrom($"revision:{commit.Manifest.Sha256}"),
            1,
            DemoIdentity.GuidFrom($"object:{commit.StoredObject.Sha256}"),
            DemoIdentity.GuidFrom($"job:{commit.Manifest.Sha256}"),
            commit.Manifest.Sha256,
            false
        );
    }
}
