using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class DocumentEvidenceFacade
{
    private readonly IDocumentAccessPolicy _accessPolicy;
    private readonly IGeneratedOperationalStore _store;

    public DocumentEvidenceFacade(
        IDocumentAccessPolicy accessPolicy,
        IGeneratedOperationalStore store
    )
    {
        _accessPolicy = accessPolicy;
        _store = store;
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
        return await _store.ListFragmentsAsync(
            query.WorkspaceId,
            query.RevisionId,
            cancellationToken
        );
    }
}
