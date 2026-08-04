namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal static class AppForgeResponseScripts
{
    public static HttpResponseMessage Revision(
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

    public static HttpResponseMessage Document(
        HttpRequestMessage request,
        Guid documentId,
        Guid workspaceId,
        int currentRevisionNumber = 1
    )
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
            currentRevisionNumber,
            isRevoked = false,
        });
    }

    public static HttpResponseMessage FragmentPage(
        HttpRequestMessage request,
        Guid revisionId,
        int page,
        int sequence
    )
    {
        var uri = request.RequestUri!;
        TestAssert.Equal("/api/documentfragments", uri.AbsolutePath, "Fragment route drifted.");
        DemandQueryPart(uri, "filters%5B0%5D.field=DocumentRevisionId", "filter field");
        DemandQueryPart(uri, "filters%5B0%5D.operator=equals", "filter operator");
        DemandQueryPart(uri, $"filters%5B0%5D.value={revisionId:D}", "filter value");
        DemandQueryPart(uri, "sort%5B0%5D.field=Sequence", "sequence sort");
        DemandQueryPart(uri, $"page={page}", "page");

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
                    contentHash = sequence == 0 ? new string('a', 64) : new string('b', 64),
                },
            },
            page,
            pageSize = 100,
            totalCount = 2,
        });
    }

    private static void DemandQueryPart(Uri uri, string expected, string label)
    {
        TestAssert.True(
            uri.Query.Contains(expected, StringComparison.Ordinal),
            $"Generated fragment {label} is missing."
        );
    }
}
