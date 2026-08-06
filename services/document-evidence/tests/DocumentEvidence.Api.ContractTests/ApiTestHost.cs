using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.DependencyInjection;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal sealed class ApiTestHost : IAsyncDisposable
{
    private readonly WebApplication _application;

    private ApiTestHost(
        WebApplication application,
        HttpClient client,
        FakeDocumentEvidenceApiOperations operations,
        FakeReadPlanApiOperations readPlans
    )
    {
        _application = application;
        Client = client;
        Operations = operations;
        ReadPlans = readPlans;
    }

    public HttpClient Client { get; }
    public FakeDocumentEvidenceApiOperations Operations { get; }
    public FakeReadPlanApiOperations ReadPlans { get; }

    public static async Task<ApiTestHost> StartAsync()
    {
        var operations = new FakeDocumentEvidenceApiOperations();
        var readPlans = new FakeReadPlanApiOperations();
        var builder = WebApplication.CreateBuilder();
        builder.WebHost.UseUrls("http://127.0.0.1:0");
        builder.Services.AddSingleton<IDocumentEvidenceApiOperations>(operations);
        builder.Services.AddSingleton<IDocumentEvidenceReadPlanApiOperations>(readPlans);
        var application = builder.Build();
        application.MapDocumentEvidenceV1();
        await application.StartAsync();

        var server = application.Services.GetRequiredService<IServer>();
        var addresses = server.Features.Get<IServerAddressesFeature>()?.Addresses;
        var address = addresses?.SingleOrDefault()
            ?? throw new InvalidOperationException("Loopback API address was not assigned.");
        var client = new HttpClient { BaseAddress = new Uri(address) };
        return new ApiTestHost(application, client, operations, readPlans);
    }

    public async ValueTask DisposeAsync()
    {
        Client.Dispose();
        await _application.StopAsync();
        await _application.DisposeAsync();
    }
}
