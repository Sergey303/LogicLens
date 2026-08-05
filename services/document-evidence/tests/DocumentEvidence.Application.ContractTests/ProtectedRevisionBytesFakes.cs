using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal sealed class ProtectedReadFixture
{
    private readonly Guid _actorId = Guid.NewGuid();
    private readonly Guid _workspaceId = Guid.NewGuid();
    private readonly Guid _revisionId = Guid.NewGuid();
    private readonly ProtectedRevisionBytesService _service;

    public ProtectedReadFixture(bool deny, bool revoked)
    {
        Events = [];
        _service = new ProtectedRevisionBytesService(
            new ProtectedAccessPolicy(Events, deny),
            new ProtectedObjectLocator(Events, _workspaceId, _revisionId, revoked),
            new ProtectedObjectStore(Events)
        );
    }

    public List<string> Events { get; }

    public Task<Stream> OpenAsync() => _service.OpenAsync(
        new OpenRevisionBytesQuery(_actorId, _workspaceId, _revisionId)
    );
}

internal sealed class ProtectedAccessPolicy : IDocumentAccessPolicy
{
    private readonly List<string> _events;
    private readonly bool _deny;

    public ProtectedAccessPolicy(List<string> events, bool deny)
    {
        _events = events;
        _deny = deny;
    }

    public ValueTask DemandRevisionReadAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("access");
        return _deny
            ? ValueTask.FromException(new UnauthorizedAccessException())
            : ValueTask.CompletedTask;
    }

    public ValueTask DemandDocumentReadAsync(
        Guid actorId,
        DocumentKey key,
        CancellationToken cancellationToken
    ) => ValueTask.CompletedTask;
}

internal sealed class ProtectedObjectLocator : IProtectedRevisionObjectLocator
{
    private readonly List<string> _events;
    private readonly ProtectedRevisionObject _value;

    public ProtectedObjectLocator(List<string> events, Guid workspaceId, Guid revisionId, bool revoked)
    {
        _events = events;
        _value = new ProtectedRevisionObject(
            workspaceId,
            Guid.NewGuid(),
            revisionId,
            new string('a', 64),
            3,
            "application/pdf",
            revoked
        );
    }

    public Task<ProtectedRevisionObject?> FindAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        _events.Add("locator");
        return Task.FromResult<ProtectedRevisionObject?>(_value);
    }
}

internal sealed class ProtectedObjectStore : IImmutableObjectStore
{
    private readonly List<string> _events;

    public ProtectedObjectStore(List<string> events)
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
