using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class MutableReadPlanAccessPolicy : IDocumentAccessPolicy
{
    private readonly List<string> _events;

    public MutableReadPlanAccessPolicy(List<string> events)
    {
        _events = events;
    }

    public bool Deny { get; set; }

    public ValueTask DemandRevisionReadAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("access");
        return Deny
            ? ValueTask.FromException(new UnauthorizedAccessException())
            : ValueTask.CompletedTask;
    }

    public ValueTask DemandDocumentReadAsync(
        Guid actorId,
        DocumentKey key,
        CancellationToken cancellationToken
    ) => ValueTask.CompletedTask;
}

internal sealed class MutableReadPlanLocator : IProtectedRevisionObjectLocator
{
    private readonly List<string> _events;

    public MutableReadPlanLocator(List<string> events, ProtectedRevisionObject value)
    {
        _events = events;
        Value = value;
    }

    public ProtectedRevisionObject Value { get; set; }

    public Task<ProtectedRevisionObject?> FindAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("locator");
        return Task.FromResult<ProtectedRevisionObject?>(Value);
    }
}

internal sealed class RecordingReadPlanStore : IImmutableObjectStore
{
    private readonly List<string> _events;

    public RecordingReadPlanStore(List<string> events)
    {
        _events = events;
    }

    public Task<StoredObjectReference> PutAsync(Stream content, CancellationToken cancellationToken) =>
        throw new NotSupportedException();

    public Task<Stream> OpenReadAsync(string sha256, CancellationToken cancellationToken)
    {
        _events.Add("object");
        return Task.FromResult<Stream>(new MemoryStream([1, 2, 3], writable: false));
    }
}

internal sealed class RecordingReadPlanProtector : IRevisionReadPlanProtector
{
    private RevisionReadPlanPayload? _payload;

    public string Protect(RevisionReadPlanPayload payload)
    {
        _payload = payload;
        return "signed-read-plan";
    }

    public RevisionReadPlanPayload Unprotect(string token)
    {
        return token == "signed-read-plan" && _payload is not null
            ? _payload
            : throw new UnauthorizedAccessException("Invalid test token.");
    }
}

internal sealed class MutableTimeProvider : TimeProvider
{
    public MutableTimeProvider(DateTimeOffset utcNow)
    {
        UtcNow = utcNow;
    }

    public DateTimeOffset UtcNow { get; private set; }

    public override DateTimeOffset GetUtcNow() => UtcNow;

    public void Advance(TimeSpan value)
    {
        UtcNow = UtcNow.Add(value);
    }
}
