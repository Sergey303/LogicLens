using System.Net;
using System.Net.Http.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal static class ReadPlanHttpNegativeContractTests
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");

    public static async Task MissingTokenStopsBeforeOperationAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        using var request = CreateRequest();
        using var response = await host.Client.SendAsync(request);

        TestAssert.Equal(HttpStatusCode.BadRequest, response.StatusCode, "Missing token status is wrong.");
        var error = await response.Content.ReadFromJsonAsync<DocumentEvidenceErrorDto>();
        TestAssert.Equal("missing-header", error?.Code, "Missing token error code is wrong.");
        TestAssert.True(host.ReadPlans.OpenedActorId is null, "Missing token must stop before operation.");
    }

    public static async Task OversizedTokenStopsBeforeOperationAsync()
    {
        await using var host = await ApiTestHost.StartAsync();
        using var request = CreateRequest();
        request.Headers.TryAddWithoutValidation(
            DocumentEvidenceApiV1.ReadPlanTokenHeader,
            new string('x', 4097)
        );
        using var response = await host.Client.SendAsync(request);

        TestAssert.Equal(HttpStatusCode.BadRequest, response.StatusCode, "Oversized token status is wrong.");
        var error = await response.Content.ReadFromJsonAsync<DocumentEvidenceErrorDto>();
        TestAssert.Equal("invalid-header", error?.Code, "Oversized token error code is wrong.");
        TestAssert.True(host.ReadPlans.OpenedActorId is null, "Oversized token must stop before operation.");
    }

    private static HttpRequestMessage CreateRequest()
    {
        var request = new HttpRequestMessage(HttpMethod.Get, DocumentEvidenceApiV1.ReadPlanContent());
        request.Headers.TryAddWithoutValidation(
            DocumentEvidenceApiV1.ActorHeader,
            ActorId.ToString("D")
        );
        return request;
    }
}
