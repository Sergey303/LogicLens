using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class ProtectedRevisionBytesService
{
    private readonly IDocumentAccessPolicy _accessPolicy;
    private readonly IProtectedRevisionObjectLocator _locator;
    private readonly IImmutableObjectStore _objectStore;

    public ProtectedRevisionBytesService(
        IDocumentAccessPolicy accessPolicy,
        IProtectedRevisionObjectLocator locator,
        IImmutableObjectStore objectStore
    )
    {
        _accessPolicy = accessPolicy ?? throw new ArgumentNullException(nameof(accessPolicy));
        _locator = locator ?? throw new ArgumentNullException(nameof(locator));
        _objectStore = objectStore ?? throw new ArgumentNullException(nameof(objectStore));
    }

    public async Task<Stream> OpenAsync(
        OpenRevisionBytesQuery query,
        CancellationToken cancellationToken = default
    )
    {
        await _accessPolicy.DemandRevisionReadAsync(
            query.ActorId,
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        );
        var revision = await _locator.FindAsync(
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        ) ?? throw new FileNotFoundException("Document revision was not found.");
        if (revision.WorkspaceId != query.WorkspaceId || revision.RevisionId != query.RevisionId)
        {
            throw new InvalidDataException("Revision locator returned a mismatched identity.");
        }
        if (revision.IsRevoked || revision.IsSuperseded)
        {
            throw new UnauthorizedAccessException("Document revision is no longer readable.");
        }
        return await _objectStore.OpenReadAsync(revision.Sha256, cancellationToken);
    }
}
