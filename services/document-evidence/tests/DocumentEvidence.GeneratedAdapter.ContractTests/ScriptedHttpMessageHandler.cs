using System.Net;
using System.Text;
using System.Text.Json;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter.ContractTests;

internal sealed class ScriptedHttpMessageHandler : HttpMessageHandler
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly Queue<Func<HttpRequestMessage, HttpResponseMessage>> _steps = new();

    public void Add(Func<HttpRequestMessage, HttpResponseMessage> step)
    {
        _steps.Enqueue(step);
    }

    public void AssertComplete()
    {
        TestAssert.Equal(0, _steps.Count, "Not all expected HTTP calls were executed.");
    }

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken
    )
    {
        if (_steps.Count == 0)
        {
            throw new InvalidOperationException($"Unexpected HTTP call: {request.Method} {request.RequestUri}");
        }

        return Task.FromResult(_steps.Dequeue()(request));
    }

    public static HttpResponseMessage Json(object payload, HttpStatusCode status = HttpStatusCode.OK)
    {
        var json = JsonSerializer.Serialize(payload, JsonOptions);
        return new HttpResponseMessage(status)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json"),
        };
    }
}
