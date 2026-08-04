using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal static class AdapterContractTests
{
    public static async Task FindDocumentMapsExpectedRouteAsync()
    {
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        var handler = new ScriptedHttpMessageHandler();
        handler.Add(request => AppForgeResponseScripts.Document(
            request,
            documentId,
            workspaceId,
            currentRevisionNumber: 2
        ));

        var store = CreateStore(handler);
        var result = await store.FindDocumentAsync(
            new DocumentKey(workspaceId, documentId),
            CancellationToken.None
        );

        TestAssert.True(result is not null, "Document mapping returned null.");
        TestAssert.Equal("Evidence.pdf", result!.DisplayName, "Display name was not mapped.");
        TestAssert.Equal(2, result.CurrentRevisionNumber, "Revision number was not mapped.");
        handler.AssertComplete();
    }

    public static async Task ListFragmentsValidatesAndPaginatesAsync()
    {
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        var revisionId = Guid.NewGuid();
        var handler = new ScriptedHttpMessageHandler();
        handler.Add(request => AppForgeResponseScripts.Revision(request, revisionId, documentId));
        handler.Add(request => AppForgeResponseScripts.Document(request, documentId, workspaceId));
        handler.Add(request => AppForgeResponseScripts.FragmentPage(
            request,
            revisionId,
            page: 1,
            sequence: 0
        ));
        handler.Add(request => AppForgeResponseScripts.FragmentPage(
            request,
            revisionId,
            page: 2,
            sequence: 1
        ));

        var fragments = await CreateStore(handler).ListFragmentsAsync(
            workspaceId,
            revisionId,
            CancellationToken.None
        );

        TestAssert.Equal(2, fragments.Count, "Adapter did not read every fragment page.");
        TestAssert.Equal(0, fragments[0].Sequence, "First fragment sequence was not mapped.");
        TestAssert.Equal(1, fragments[1].Sequence, "Second fragment sequence was not mapped.");
        handler.AssertComplete();
    }

    public static async Task WorkspaceMismatchStopsBeforeFragmentLookupAsync()
    {
        var expectedWorkspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        var revisionId = Guid.NewGuid();
        var handler = new ScriptedHttpMessageHandler();
        handler.Add(request => AppForgeResponseScripts.Revision(request, revisionId, documentId));
        handler.Add(request => AppForgeResponseScripts.Document(
            request,
            documentId,
            Guid.NewGuid()
        ));
        var store = CreateStore(handler);

        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => store.ListFragmentsAsync(
                expectedWorkspaceId,
                revisionId,
                CancellationToken.None
            ),
            "Cross-workspace generated response was accepted."
        );
        handler.AssertComplete();
    }

    private static AppForgeGeneratedOperationalStore CreateStore(
        ScriptedHttpMessageHandler handler
    )
    {
        var client = new HttpClient(handler)
        {
            BaseAddress = new Uri("https://generated.test/"),
        };
        return new AppForgeGeneratedOperationalStore(client);
    }
}
