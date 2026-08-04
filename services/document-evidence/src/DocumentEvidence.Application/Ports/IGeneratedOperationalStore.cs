using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IGeneratedOperationalStore
{
    Task<DocumentSummary?> FindDocumentAsync(
        DocumentKey key,
        CancellationToken cancellationToken
    );

    Task<IReadOnlyList<FragmentSummary>> ListFragmentsAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    );
}
