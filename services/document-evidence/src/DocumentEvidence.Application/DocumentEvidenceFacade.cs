using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class DocumentEvidenceFacade
{
    private readonly IDocumentAccessPolicy _accessPolicy;
    private readonly IGeneratedOperationalStore _store;
    private readonly IProtectedRevisionObjectLocator _revisionLocator;

    public DocumentEvidenceFacade(
        IDocumentAccessPolicy accessPolicy,
        IGeneratedOperationalStore store,
        IProtectedRevisionObjectLocator revisionLocator
    )
    {
        _accessPolicy = accessPolicy ?? throw new ArgumentNullException(nameof(accessPolicy));
        _store = store ?? throw new ArgumentNullException(nameof(store));
        _revisionLocator = revisionLocator ?? throw new ArgumentNullException(nameof(revisionLocator));
    }

    public async Task<DocumentSummary?> GetDocumentAsync(
        GetDocumentQuery query,
        CancellationToken cancellationToken = default
    )
    {
        await _accessPolicy.DemandDocumentReadAsync(
            query.ActorId,
            query.Key,
            cancellationToken
        );
        return await _store.FindDocumentAsync(query.Key, cancellationToken);
    }

    public async Task<IReadOnlyList<FragmentSummary>> ListFragmentsAsync(
        ListFragmentsQuery query,
        CancellationToken cancellationToken = default
    )
    {
        await _accessPolicy.DemandRevisionReadAsync(
            query.ActorId,
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        );
        var revision = await _revisionLocator.FindAsync(
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        );
        if (revision is null)
        {
            return [];
        }
        if (revision.WorkspaceId != query.WorkspaceId || revision.RevisionId != query.RevisionId)
        {
            throw new InvalidDataException("Revision locator returned a mismatched identity.");
        }
        if (revision.IsRevoked || revision.IsSuperseded)
        {
            throw new UnauthorizedAccessException("Document revision is no longer readable.");
        }
        return await _store.ListFragmentsAsync(
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        );
    }
}
