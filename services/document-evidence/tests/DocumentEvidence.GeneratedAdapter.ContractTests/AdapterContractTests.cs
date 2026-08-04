using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal static class AdapterContractTests
{
    public static async Task FindDocumentMapsExpectedRouteAsync()
    {
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        var handler = new ScriptedHttpMessageHandler();
        handler.Add(request =>
        {
            TestAssert.Equal(HttpMethod.Get, request.Method, "Document lookup must use GET.");
            TestAssert.Equal(
                $"/api/documents/{documentId:D}",
                request.RequestUri!.PathAndQuery,
                "Document route drifted from AppForge."
            );
            return ScriptedHttpMessageHandler.Json(new
            {
                id = documentId,
                workspaceId,
                displayName = "Evidence.pdf",
                mediaType = "application/pdf",
                sourceKind = "Upload",
                state = "Ready",
                currentRevisionNumber = 2,
                isRevoked = false,
            });
        });

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
        handler.Add(request => RevisionResponse(request, revisionId, documentId));
        handler.Add(request => DocumentResponse(request, documentId, workspaceId));
        handler.Add(request => FragmentPageResponse(request, revisionId, page: 1, sequence: 0));
        handler.Add(request => FragmentPageResponse(request, revisionId, page: 2, sequence: 1));

        var store = CreateStore(handler);
        var fragments = await store.ListFragmentsAsync(
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
        handler.Add(request => RevisionResponse(request, revisionId, documentId));
        handler.Add(request => DocumentResponse(request, documentId, Guid.NewGuid()));
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

    private static HttpResponseMessage RevisionResponse(
        HttpRequestMessage request,
        Guid revisionId,
        Guid documentId
    )
    {
        TestAssert.Equal(
            $"/api/documentrevisions/{revisionId:D}",
            request.RequestUri!.PathAndQuery,
            "Revision route drifted from AppForge."
        );
        return ScriptedHttpMessageHandler.Json(new { id = revisionId, documentId });
    }

    private static HttpResponseMessage DocumentResponse(
        HttpRequestMessage request,
        Guid documentId,
        Guid workspaceId
    )
    {
        TestAssert.Equal(
            $"/api/documents/{documentId:D}",
            request.RequestUri!.PathAndQuery,
            "Document route drifted from AppForge."
        );
        return ScriptedHttpMessageHandler.Json(new
        {
            id = documentId,
            workspaceId,
            displayName = "Evidence.pdf",
            mediaType = "application/pdf",
            sourceKind = "Upload",
            state = "Ready",
            currentRevisionNumber = 1,
            isRevoked = false,
        });
    }

    private static HttpResponseMessage FragmentPageResponse(
        HttpRequestMessage request,
        Guid revisionId,
        int page,
        int sequence
    )
    {
        var uri = request.RequestUri!;
        TestAssert.Equal("/api/documentfragments", uri.AbsolutePath, "Fragment route drifted.");
        TestAssert.True(
            uri.Query.Contains($"filters%5B0%5D.value={revisionId:D}", StringComparison.Ordinal),
            "Revision equality filter is missing."
        );
        TestAssert.True(
            uri.Query.Contains($"page={page}", StringComparison.Ordinal),
            "Fragment page is missing."
        );
        return ScriptedHttpMessageHandler.Json(new
        {
            items = new[]
            {
                new
                {
                    id = Guid.NewGuid(),
                    documentRevisionId = revisionId,
                    sequence,
                    kind = "PageText",
                    anchorJson = $"{{\"page\":{sequence + 1}}}",
                    text = $"Fragment {sequence}",
                    contentHash = new string((char)('a' + sequence), 64),
                },
            },
            page,
            pageSize = 100,
            totalCount = 2,
        });
    }
}
