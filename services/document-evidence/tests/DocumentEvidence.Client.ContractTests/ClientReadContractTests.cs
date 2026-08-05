using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Client.ContractTests;

internal static class ClientReadContractTests
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid WorkspaceId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static readonly Guid DocumentId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");
    private static readonly Guid RevisionId = Guid.Parse("11111111-1111-1111-1111-111111111111");

    public static async Task NotFoundDocumentReturnsNullAsync()
    {
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.NotFound));
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);

        var result = await client.GetDocumentAsync(WorkspaceId, DocumentId);

        TestAssert.True(result is null, "HTTP 404 must map to a null document result.");
        TestAssert.Equal(
            DocumentEvidenceApiV1.Document(WorkspaceId, DocumentId),
            new Uri(handler.Requests.Single().Url).PathAndQuery,
            "Document route is wrong."
        );
    }

    public static async Task FragmentAnchorRemainsTypedJsonAsync()
    {
        using var anchorDocument = JsonDocument.Parse(
            "{\"page\":1,\"blockId\":\"pdf:block-1\"}"
        );
        var fragment = new DocumentFragmentDto(
            Guid.Parse("22222222-2222-2222-2222-222222222222"),
            RevisionId,
            1,
            "pdf-block",
            new FragmentAnchorDto("pdf-block", anchorDocument.RootElement.Clone()),
            "Rated power: 120 W",
            new string('b', 64)
        );
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = JsonContent.Create<IReadOnlyList<DocumentFragmentDto>>([fragment]),
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);

        var result = await client.ListFragmentsAsync(WorkspaceId, RevisionId);

        TestAssert.Equal(1, result.Count, "Fragment response count is wrong.");
        TestAssert.Equal(
            "pdf:block-1",
            result[0].Anchor.Value.GetProperty("blockId").GetString(),
            "Typed fragment anchor was lost."
        );
        TestAssert.Equal(
            DocumentEvidenceApiV1.Fragments(WorkspaceId, RevisionId),
            new Uri(handler.Requests.Single().Url).PathAndQuery,
            "Fragment route is wrong."
        );
    }
}
