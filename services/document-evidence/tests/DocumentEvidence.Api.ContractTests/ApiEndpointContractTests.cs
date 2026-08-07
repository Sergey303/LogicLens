using System.Net;
using System.Net.Http.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Client;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal static class ApiEndpointContractTests
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid WorkspaceId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static readonly Guid DocumentId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");
    private static readonly Guid RevisionId = Guid.Parse("11111111-1111-1111-1111-111111111111");

    public static async Task GeneratedClientTraversesRealEndpointsAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        var client = new DocumentEvidenceClient(host.Client, ActorId);
        var bytes = "%PDF-1.4\nHTTP fixture"u8.ToArray();
        using var content = new MemoryStream(bytes, writable: false);

        var upload = await client.UploadRevisionAsync(
            WorkspaceId,
            DocumentId,
            "demo.pdf",
            "http-demo-001",
            "application/pdf",
            content,
            bytes.LongLength
        );
        var document = await client.GetDocumentAsync(WorkspaceId, DocumentId);
        var fragments = await client.ListFragmentsAsync(WorkspaceId, upload.RevisionId);

        TestAssert.Equal("Pending", upload.ProcessingState, "Upload state is wrong.");
        TestAssert.Equal("Ready", document?.State, "Document state is wrong.");
        TestAssert.Equal(1, fragments.Count, "Fragment count is wrong.");
        TestAssert.Equal(
            "pdf:block-1",
            fragments[0].Anchor.Value.GetProperty("blockId").GetString(),
            "Typed HTTP anchor was lost."
        );
        var request = host.Operations.UploadRequest
            ?? throw new InvalidOperationException("Upload operation was not called.");
        TestAssert.Equal(ActorId, request.ActorId, "Actor header did not reach the operation.");
        TestAssert.Equal("demo.pdf", request.DisplayName, "File name header was lost.");
        using var output = new MemoryStream();
        await request.Content.CopyToAsync(output);
        TestAssert.True(output.ToArray().SequenceEqual(bytes), "Raw upload bytes changed.");
    }

    public static async Task ReadPlanTraversesHeaderOnlyStreamingBoundaryAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        var client = new DocumentEvidenceClient(host.Client, ActorId);

        var plan = await client.IssueReadPlanAsync(WorkspaceId, RevisionId);
        await using var stream = await client.OpenReadPlanAsync(plan.Token);
        using var output = new MemoryStream();
        await stream.CopyToAsync(output);

        TestAssert.Equal(WorkspaceId, plan.WorkspaceId, "Read plan workspace is wrong.");
        TestAssert.Equal(RevisionId, plan.RevisionId, "Read plan revision is wrong.");
        TestAssert.Equal(FakeReadPlanApiOperations.Token, plan.Token, "Read plan token changed.");
        TestAssert.Equal(ActorId, host.ReadPlans.IssuedActorId, "Issue actor was lost.");
        TestAssert.Equal(ActorId, host.ReadPlans.OpenedActorId, "Execution actor was lost.");
        TestAssert.Equal(plan.Token, host.ReadPlans.OpenedToken, "Token header was lost.");
        TestAssert.True(
            output.ToArray().SequenceEqual(FakeReadPlanApiOperations.Bytes),
            "Read plan bytes changed across HTTP streaming."
        );
    }

    public static async Task ReadPlanResponsesAreNeverCacheableAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        using var issueRequest = new HttpRequestMessage(
            HttpMethod.Post,
            DocumentEvidenceApiV1.ReadPlan(WorkspaceId, RevisionId)
        );
        issueRequest.Headers.TryAddWithoutValidation(
            DocumentEvidenceApiV1.ActorHeader,
            ActorId.ToString("D")
        );
        using var issueResponse = await host.Client.SendAsync(issueRequest);
        TestAssert.True(
            issueResponse.Headers.CacheControl?.NoStore == true,
            "Read plan tokens must never be stored by HTTP caches."
        );

        using var openRequest = new HttpRequestMessage(
            HttpMethod.Get,
            DocumentEvidenceApiV1.ReadPlanContent()
        );
        openRequest.Headers.TryAddWithoutValidation(
            DocumentEvidenceApiV1.ActorHeader,
            ActorId.ToString("D")
        );
        openRequest.Headers.TryAddWithoutValidation(
            DocumentEvidenceApiV1.ReadPlanTokenHeader,
            FakeReadPlanApiOperations.Token
        );
        using var openResponse = await host.Client.SendAsync(
            openRequest,
            HttpCompletionOption.ResponseHeadersRead
        );
        TestAssert.True(
            openResponse.Headers.CacheControl?.NoStore == true &&
                openResponse.Headers.CacheControl.Private,
            "Read plan bytes must be private and never cacheable."
        );
    }

    public static async Task MissingActorHeaderReturnsTypedBadRequestAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        using var request = new HttpRequestMessage(
            HttpMethod.Get,
            DocumentEvidenceApiV1.Document(WorkspaceId, DocumentId)
        );
        using var response = await host.Client.SendAsync(request);

        TestAssert.Equal(HttpStatusCode.BadRequest, response.StatusCode, "Missing actor status is wrong.");
        var error = await response.Content.ReadFromJsonAsync<DocumentEvidenceErrorDto>();
        TestAssert.Equal("missing-header", error?.Code, "Missing actor error code is wrong.");
        TestAssert.True(error?.Retryable == false, "Missing actor error cannot be retryable.");
    }
}
