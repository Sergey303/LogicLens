namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

internal static class AppForgeGeneratedRoutes
{
    private const int FragmentPageSize = 100;

    public static string Document(Guid documentId)
    {
        return $"api/documents/{documentId:D}";
    }

    public static string Revision(Guid revisionId)
    {
        return $"api/documentrevisions/{revisionId:D}";
    }

    public static string FragmentPage(Guid revisionId, int page)
    {
        return string.Join(
            "&",
            "api/documentfragments?filters%5B0%5D.field=DocumentRevisionId",
            "filters%5B0%5D.operator=equals",
            $"filters%5B0%5D.value={revisionId:D}",
            $"page={page}",
            $"pageSize={FragmentPageSize}",
            "sort%5B0%5D.field=Sequence",
            "sort%5B0%5D.direction=asc"
        );
    }
}
