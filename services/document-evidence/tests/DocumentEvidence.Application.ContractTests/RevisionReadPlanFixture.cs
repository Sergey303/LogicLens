using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class RevisionReadPlanFixture
{
    private readonly Guid _actorId = Guid.NewGuid();
    private readonly Guid _workspaceId = Guid.NewGuid();
    private readonly Guid _documentId = Guid.NewGuid();
    private readonly Guid _revisionId = Guid.NewGuid();
    private readonly MutableReadPlanAccessPolicy _access;
    private readonly MutableReadPlanLocator _locator;
    private readonly MutableTimeProvider _time;
    private readonly RevisionReadPlanService _service;

    public RevisionReadPlanFixture()
    {
        Events = [];
        _access = new MutableReadPlanAccessPolicy(Events);
        _locator = new MutableReadPlanLocator(Events, CreateRevision());
        _time = new MutableTimeProvider(new DateTimeOffset(2026, 8, 6, 0, 0, 0, TimeSpan.Zero));
        _service = new RevisionReadPlanService(
            _access,
            _locator,
            new RecordingReadPlanStore(Events),
            new RecordingReadPlanProtector(),
            _time,
            TimeSpan.FromMinutes(5)
        );
    }

    public List<string> Events { get; }

    public Task<RevisionReadPlan> IssueAsync() => _service.IssueAsync(
        new IssueRevisionReadPlanCommand(_actorId, _workspaceId, _revisionId)
    );

    public Task<Stream> OpenAsync(RevisionReadPlan plan) => _service.OpenAsync(
        new ExecuteRevisionReadPlanCommand(_actorId, plan.Token)
    );

    public void ClearEvents() => Events.Clear();

    public void DenyAccess() => _access.Deny = true;

    public void Revoke() => _locator.Value = _locator.Value with { IsRevoked = true };

    public void Supersede() => _locator.Value = _locator.Value with { IsSuperseded = true };

    public void ChangeObjectHash() => _locator.Value = _locator.Value with
    {
        Sha256 = new string('b', 64)
    };

    public void Expire() => _time.Advance(TimeSpan.FromMinutes(6));

    private ProtectedRevisionObject CreateRevision()
    {
        return new ProtectedRevisionObject(
            _workspaceId,
            _documentId,
            _revisionId,
            1,
            new string('a', 64),
            3,
            "application/pdf",
            false,
            false
        );
    }
}
