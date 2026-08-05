using KnowledgePilot.LogicLens.DocumentEvidence.Api;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.DependencyInjection;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoServiceHost : IAsyncDisposable
{
    private readonly WebApplication _application;

    private DemoServiceHost(WebApplication application, HttpClient client)
    {
        _application = application;
        Client = client;
    }

    public HttpClient Client { get; }

    public static async Task<DemoServiceHost> StartAsync(string objectRoot)
    {
        var operations = new DemoDocumentEvidenceOperations(objectRoot);
        var builder = WebApplication.CreateBuilder();
        builder.WebHost.UseUrls("http://127.0.0.1:0");
        builder.Services.AddSingleton<IDocumentEvidenceApiOperations>(operations);
        var application = builder.Build();
        application.MapDocumentEvidenceV1();
        await application.StartAsync();

        var server = application.Services.GetRequiredService<IServer>();
        var addresses = server.Features.Get<IServerAddressesFeature>()?.Addresses;
        var address = addresses?.SingleOrDefault()
            ?? throw new InvalidOperationException("Demo loopback address was not assigned.");
        return new DemoServiceHost(
            application,
            new HttpClient { BaseAddress = new Uri(address) }
        );
    }

    public async ValueTask DisposeAsync()
    {
        Client.Dispose();
        await _application.StopAsync();
        await _application.DisposeAsync();
    }
}
