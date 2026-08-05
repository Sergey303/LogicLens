using System.Net;
using System.Net.Http.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Client.ContractTests;

internal static class ClientUploadContractTests
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid WorkspaceId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static readonly Guid DocumentId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");

    public static async Task UploadUsesVersionedRouteHeadersAndRawBytesAsync()
    {
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.Created)
        {
            Content = JsonContent.Create(new UploadRevisionDto(
                WorkspaceId,
                DocumentId,
                Guid.Parse("11111111-1111-1111-1111-111111111111"),
                1,
                Guid.Parse("22222222-2222-2222-2222-222222222222"),
                new string('a', 64),
                "demo.pdf",
                "Pending",
                false
            )),
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);
        var bytes = "%PDF-1.4\nclient fixture"u8.ToArray();
        using var stream = new MemoryStream(bytes, writable: false);

        var result = await client.UploadRevisionAsync(
            WorkspaceId,
            DocumentId,
            "demo.pdf",
            "demo-001",
            "application/pdf",
            stream,
            bytes.LongLength
        );

        TestAssert.Equal("Pending", result.ProcessingState, "Upload response state is wrong.");
        TestAssert.True(stream.CanRead, "Generated client must not dispose caller-owned content.");
        var request = handler.Requests.Single();
        TestAssert.Equal(HttpMethod.Put, request.Method, "Upload HTTP method is wrong.");
        TestAssert.Equal(
            DocumentEvidenceApiV1.UploadRevision(WorkspaceId, DocumentId),
            new Uri(request.Url).PathAndQuery,
            "Upload route is wrong."
        );
        TestAssert.Equal(ActorId.ToString("D"), request.Headers[DocumentEvidenceApiV1.ActorHeader], "Actor header is wrong.");
        TestAssert.Equal("demo.pdf", request.Headers[DocumentEvidenceApiV1.FileNameHeader], "File name header is wrong.");
        TestAssert.Equal("demo-001", request.Headers[DocumentEvidenceApiV1.IdempotencyHeader], "Idempotency header is wrong.");
        TestAssert.True(request.Content.SequenceEqual(bytes), "Upload bytes changed in transport.");
    }

    public static async Task TypedQuotaErrorIsPreservedAsync()
    {
        var handler = new ScriptedHttpMessageHandler();
        handler.Enqueue(_ => new HttpResponseMessage(HttpStatusCode.TooManyRequests)
        {
            Content = JsonContent.Create(new DocumentEvidenceErrorDto(
                "daily-byte-limit",
                "The upload quota has been exceeded.",
                true
            )),
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://service/") };
        var client = new DocumentEvidenceClient(http, ActorId);
        using var stream = new MemoryStream("%PDF-"u8.ToArray(), writable: false);

        var error = await TestAssert.ThrowsAsync<DocumentEvidenceClientException>(
            () => client.UploadRevisionAsync(
                WorkspaceId,
                DocumentId,
                "demo.pdf",
                "demo-002",
                "application/pdf",
                stream
            ),
            "Generated client must throw a typed quota error."
        );

        TestAssert.Equal("daily-byte-limit", error.Code, "Typed error code was lost.");
        TestAssert.True(error.Retryable, "Retryable error flag was lost.");
    }
}
