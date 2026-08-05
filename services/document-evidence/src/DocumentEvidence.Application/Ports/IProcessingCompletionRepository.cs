using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IProcessingCompletionRepository
{
    Task<bool> TryCompleteAsync(
        ProcessingJobSnapshot expectedJob,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    );
}
