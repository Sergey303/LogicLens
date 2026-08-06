using System.Net;
using System.Net.Http.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Client.ContractTests;

internal static class ClientReadPlanContractTests
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid WorkspaceId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static readonly Guid DocumentId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");
    private static readonly Guid RevisionId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private const string Token = "signed.read.plan.token";

    public static async Task IssueUsesVersionedPostAndReturnsTypedTokenAsync()
    {
        var dto = new ReadPlanDto(
            Guid.Parse("44444444-4444-4444-4444-444444444444"),
            WorkspaceId,
            DocumentId,
            RevisionId,
            1,
            DateTimeOffset.Parse("2026-08-07T00:30:00Z"),
            "application/pdf",
            3,
            new string('c', 64),
            Token
        );
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.Created)
        {
            Content = JsonContent.Create(dto),
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);

        var result = await client.IssueReadPlanAsync(WorkspaceId, RevisionId);

        var request = handler.Requests.Single();
        TestAssert.Equal(HttpMethod.Post, request.Method, "Read plan issue method is wrong.");
        TestAssert.Equal(
            DocumentEvidenceApiV1.ReadPlan(WorkspaceId, RevisionId),
            new Uri(request.Url).PathAndQuery,
            "Read plan issue route is wrong."
        );
        TestAssert.Equal(Token, result.Token, "Typed read plan token was lost.");
    }

    public static async Task OpenUsesHeaderOnlyAndOwnsResponseLifetimeAsync()
    {
        var content = new TrackingByteArrayContent([1, 2, 3]);
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.OK) { Content = content });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);

        await using (var stream = await client.OpenReadPlanAsync(Token))
        {
            TestAssert.True(!content.IsDisposed, "Response closed before the caller read its stream.");
            using var output = new MemoryStream();
            await stream.CopyToAsync(output);
            TestAssert.True(output.ToArray().SequenceEqual([1, 2, 3]), "Stream bytes changed.");
        }

        var request = handler.Requests.Single();
        TestAssert.Equal(
            DocumentEvidenceApiV1.ReadPlanContent(),
            new Uri(request.Url).PathAndQuery,
            "Read plan content route is wrong."
        );
        TestAssert.True(!request.Url.Contains(Token, StringComparison.Ordinal), "Token leaked into URL.");
        TestAssert.Equal(
            Token,
            request.Headers[DocumentEvidenceApiV1.ReadPlanTokenHeader],
            "Read plan token header is wrong."
        );
        TestAssert.True(content.IsDisposed, "Closing the stream must dispose the HTTP response.");
    }
}

internal sealed class TrackingByteArrayContent(byte[] bytes) : ByteArrayContent(bytes)
{
    public bool IsDisposed { get; private set; }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            IsDisposed = true;
        }
        base.Dispose(disposing);
    }
}
