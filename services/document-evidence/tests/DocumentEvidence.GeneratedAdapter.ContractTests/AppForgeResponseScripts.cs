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
}
