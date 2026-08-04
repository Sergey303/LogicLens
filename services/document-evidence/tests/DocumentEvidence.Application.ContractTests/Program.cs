using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await AllowsStoreLookupOnlyAfterAuthorizationAsync();
        await DenialPreventsStoreLookupAsync();
        await UploadServiceContractTests.ReplayAvoidsObjectWriteAsync();
        await UploadServiceContractTests.NewUploadBuildsDeterministicManifestAsync();
        await UploadServiceContractTests.ConflictingCommitResultIsRejectedAsync();
        Console.WriteLine("Document Evidence boundary contract tests passed.");
        return 0;
    }

    private static async Task AllowsStoreLookupOnlyAfterAuthorizationAsync()
    {
        var events = new List<string>();
        var key = new DocumentKey(Guid.NewGuid(), Guid.NewGuid());
        var access = new RecordingAccessPolicy(events);
        var store = new RecordingStore(events, key);
        var facade = new DocumentEvidenceFacade(access, store);

        var result = await facade.GetDocumentAsync(new GetDocumentQuery(Guid.NewGuid(), key));

        Assert(result is not null, "Authorized lookup must return the generated-store result.");
        Assert(events.SequenceEqual(["access:document", "store:document"]), "Access must run first.");
    }

    private static async Task DenialPreventsStoreLookupAsync()
    {
        var events = new List<string>();
        var key = new DocumentKey(Guid.NewGuid(), Guid.NewGuid());
        var access = new RecordingAccessPolicy(events, deny: true);
        var store = new RecordingStore(events, key);
        var facade = new DocumentEvidenceFacade(access, store);

        try
        {
            await facade.GetDocumentAsync(new GetDocumentQuery(Guid.NewGuid(), key));
            throw new InvalidOperationException("Denied lookup unexpectedly succeeded.");
        }
        catch (UnauthorizedAccessException)
        {
            Assert(events.SequenceEqual(["access:document"]), "Store must not run after denial.");
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}

internal sealed class RecordingAccessPolicy : IDocumentAccessPolicy
{
    private readonly bool _deny;
    private readonly List<string> _events;

    public RecordingAccessPolicy(List<string> events, bool deny = false)
    {
        _events = events;
        _deny = deny;
    }

    public ValueTask DemandDocumentReadAsync(
        Guid actorId,
        DocumentKey key,
        CancellationToken cancellationToken
    )
    {
        _events.Add("access:document");
        if (_deny)
        {
            throw new UnauthorizedAccessException();
        }
        return ValueTask.CompletedTask;
    }

    public ValueTask DemandRevisionReadAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    ) => ValueTask.CompletedTask;
}

internal sealed class RecordingStore : IGeneratedOperationalStore
{
    private readonly List<string> _events;
    private readonly DocumentKey _key;

    public RecordingStore(List<string> events, DocumentKey key)
    {
        _events = events;
        _key = key;
    }

    public Task<DocumentSummary?> FindDocumentAsync(
        DocumentKey key,
        CancellationToken cancellationToken
    )
    {
        _events.Add("store:document");
        DocumentSummary result = new(_key, "Evidence", "application/pdf", "Upload", "Ready", 1, false);
        return Task.FromResult<DocumentSummary?>(result);
    }

    public Task<IReadOnlyList<FragmentSummary>> ListFragmentsAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    ) => Task.FromResult<IReadOnlyList<FragmentSummary>>([]);
}
