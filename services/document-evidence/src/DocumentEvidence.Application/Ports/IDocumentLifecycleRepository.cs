using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IDocumentLifecycleRepository
{
    Task<UploadCompletionResult?> FindUploadCompletionAsync(
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    );

    Task<UploadCompletionResult> CommitUploadAndEnqueueProcessingAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    );
}
