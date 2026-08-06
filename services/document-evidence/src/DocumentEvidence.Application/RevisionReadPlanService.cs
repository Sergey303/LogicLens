using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class RevisionReadPlanService
{
    private static readonly TimeSpan DefaultTimeToLive = TimeSpan.FromMinutes(5);
    private static readonly TimeSpan MaximumTimeToLive = TimeSpan.FromMinutes(15);
    private readonly IDocumentAccessPolicy _accessPolicy;
    private readonly IProtectedRevisionObjectLocator _locator;
    private readonly IImmutableObjectStore _objectStore;
    private readonly IRevisionReadPlanProtector _protector;
    private readonly TimeProvider _timeProvider;
    private readonly TimeSpan _timeToLive;

    public RevisionReadPlanService(
        IDocumentAccessPolicy accessPolicy,
        IProtectedRevisionObjectLocator locator,
        IImmutableObjectStore objectStore,
        IRevisionReadPlanProtector protector,
        TimeProvider? timeProvider = null,
        TimeSpan? timeToLive = null
    )
    {
        _accessPolicy = accessPolicy ?? throw new ArgumentNullException(nameof(accessPolicy));
        _locator = locator ?? throw new ArgumentNullException(nameof(locator));
        _objectStore = objectStore ?? throw new ArgumentNullException(nameof(objectStore));
        _protector = protector ?? throw new ArgumentNullException(nameof(protector));
        _timeProvider = timeProvider ?? TimeProvider.System;
        _timeToLive = timeToLive ?? DefaultTimeToLive;
        if (_timeToLive <= TimeSpan.Zero || _timeToLive > MaximumTimeToLive)
        {
            throw new ArgumentOutOfRangeException(nameof(timeToLive));
        }
    }

    public async Task<RevisionReadPlan> IssueAsync(
        IssueRevisionReadPlanCommand command,
        CancellationToken cancellationToken = default
    )
    {
        await DemandAccessAsync(command.ActorId, command.WorkspaceId, command.RevisionId,
            cancellationToken);
        var revision = await LoadUsableRevisionAsync(
            command.WorkspaceId,
            command.RevisionId,
            cancellationToken
        );
        var issuedAt = _timeProvider.GetUtcNow();
        var payload = new RevisionReadPlanPayload(
            1,
            Guid.NewGuid(),
            command.ActorId,
            revision.WorkspaceId,
            revision.DocumentId,
            revision.RevisionId,
            revision.RevisionNumber,
            revision.Sha256,
            revision.SizeBytes,
            revision.MediaType,
            issuedAt,
            issuedAt.Add(_timeToLive)
        );
        return new RevisionReadPlan(
            _protector.Protect(payload),
            payload.PlanId,
            payload.WorkspaceId,
            payload.DocumentId,
            payload.RevisionId,
            payload.RevisionNumber,
            payload.ObjectSha256,
            payload.SizeBytes,
            payload.MediaType,
            payload.ExpiresAtUtc
        );
    }

    public async Task<Stream> OpenAsync(
        ExecuteRevisionReadPlanCommand command,
        CancellationToken cancellationToken = default
    )
    {
        var payload = _protector.Unprotect(command.Token);
        var now = _timeProvider.GetUtcNow();
        if (payload.ActorId != command.ActorId || payload.ExpiresAtUtc <= now)
        {
            throw new UnauthorizedAccessException("Revision read plan is not valid for this request.");
        }
        await DemandAccessAsync(
            command.ActorId,
            payload.WorkspaceId,
            payload.RevisionId,
            cancellationToken
        );
        var revision = await LoadUsableRevisionAsync(
            payload.WorkspaceId,
            payload.RevisionId,
            cancellationToken
        );
        EnsureSnapshot(payload, revision);
        return await _objectStore.OpenReadAsync(revision.Sha256, cancellationToken);
    }

    private ValueTask DemandAccessAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    ) => _accessPolicy.DemandRevisionReadAsync(
        actorId,
        workspaceId,
        revisionId,
        cancellationToken
    );

    private async Task<ProtectedRevisionObject> LoadUsableRevisionAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        var revision = await _locator.FindAsync(workspaceId, revisionId, cancellationToken)
            ?? throw new FileNotFoundException("Document revision was not found.");
        if (revision.WorkspaceId != workspaceId || revision.RevisionId != revisionId)
        {
            throw new InvalidDataException("Revision locator returned a mismatched identity.");
        }
        if (revision.IsRevoked || revision.IsSuperseded)
        {
            throw new UnauthorizedAccessException("Document revision is no longer readable.");
        }
        return revision;
    }

    private static void EnsureSnapshot(
        RevisionReadPlanPayload payload,
        ProtectedRevisionObject revision
    )
    {
        if (payload.Version != 1 || payload.DocumentId != revision.DocumentId ||
            payload.RevisionNumber != revision.RevisionNumber ||
            !StringComparer.Ordinal.Equals(payload.ObjectSha256, revision.Sha256) ||
            payload.SizeBytes != revision.SizeBytes ||
            !StringComparer.Ordinal.Equals(payload.MediaType, revision.MediaType))
        {
            throw new UnauthorizedAccessException("Revision read plan metadata is stale.");
        }
    }
}
