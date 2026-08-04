using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IDocumentAccessPolicy
{
    ValueTask DemandDocumentReadAsync(
        Guid actorId,
        DocumentKey key,
        CancellationToken cancellationToken
    );

    ValueTask DemandRevisionReadAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    );
}
