using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IProcessingJobRepository
{
    Task<ProcessingJobSnapshot?> FindNextAvailableAsync(
        DateTimeOffset now,
        CancellationToken cancellationToken
    );

    Task<bool> CompareExchangeAsync(
        ProcessingJobSnapshot expected,
        ProcessingJobSnapshot replacement,
        CancellationToken cancellationToken
    );
}
