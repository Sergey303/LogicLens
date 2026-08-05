using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IProtectedRevisionObjectLocator
{
    Task<ProtectedRevisionObject?> FindAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    );
}
