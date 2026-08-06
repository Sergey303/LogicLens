using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class FacadeTestRevisionLocator : IProtectedRevisionObjectLocator
{
    public Task<ProtectedRevisionObject?> FindAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        ProtectedRevisionObject result = new(
            workspaceId,
            Guid.NewGuid(),
            revisionId,
            1,
            new string('d', 64),
            3,
            "application/pdf",
            false,
            false
        );
        return Task.FromResult<ProtectedRevisionObject?>(result);
    }
}
