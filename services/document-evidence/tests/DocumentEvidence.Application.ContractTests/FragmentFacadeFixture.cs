using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class FragmentFacadeFixture
{
    private readonly Guid _actorId = Guid.NewGuid();
    private readonly Guid _workspaceId = Guid.NewGuid();
    private readonly Guid _revisionId = Guid.NewGuid();
    private readonly MutableReadPlanAccessPolicy _access;
    private readonly MutableReadPlanLocator _locator;
    private readonly DocumentEvidenceFacade _facade;

    public FragmentFacadeFixture()
    {
        Events = [];
        _access = new MutableReadPlanAccessPolicy(Events);
        _locator = new MutableReadPlanLocator(Events, CreateRevision());
        _facade = new DocumentEvidenceFacade(
            _access,
            new RecordingFragmentStore(Events, _revisionId),
            _locator
        );
    }

    public List<string> Events { get; }

    public Task<IReadOnlyList<FragmentSummary>> ListAsync() => _facade.ListFragmentsAsync(
        new ListFragmentsQuery(_actorId, _workspaceId, _revisionId)
    );

    public void DenyAccess() => _access.Deny = true;

    public void Revoke() => _locator.Value = _locator.Value with { IsRevoked = true };

    public void Supersede() => _locator.Value = _locator.Value with { IsSuperseded = true };

    private ProtectedRevisionObject CreateRevision()
    {
        return new ProtectedRevisionObject(
            _workspaceId,
            Guid.NewGuid(),
            _revisionId,
            1,
            new string('e', 64),
            12,
            "application/pdf",
            false,
            false
        );
    }
}

internal sealed class RecordingFragmentStore : IGeneratedOperationalStore
{
    private readonly List<string> _events;
    private readonly Guid _revisionId;

    public RecordingFragmentStore(List<string> events, Guid revisionId)
    {
        _events = events;
        _revisionId = revisionId;
    }

    public Task<DocumentSummary?> FindDocumentAsync(
        DocumentKey key,
        CancellationToken cancellationToken
    ) => throw new NotSupportedException();

    public Task<IReadOnlyList<FragmentSummary>> ListFragmentsAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("fragments");
        IReadOnlyList<FragmentSummary> result =
        [
            new FragmentSummary(
                Guid.NewGuid(),
                _revisionId,
                1,
                "Text",
                "{}",
                "evidence",
                new string('f', 64)
            )
        ];
        return Task.FromResult(result);
    }
}
