namespace KnowledgePilot.LogicLens.DocumentEvidence.Client.ContractTests;

internal sealed class ScriptedHttpMessageHandler : HttpMessageHandler
{
    private readonly Queue<Func<HttpRequestMessage, HttpResponseMessage>> _responses = [];

    public List<CapturedRequest> Requests { get; } = [];

    public void Enqueue(Func<HttpRequestMessage, HttpResponseMessage> response)
    {
        _responses.Enqueue(response);
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken
    )
    {
        if (_responses.Count == 0)
        {
            throw new InvalidOperationException("No scripted HTTP response remains.");
        }
        var content = request.Content is null
            ? []
            : await request.Content.ReadAsByteArrayAsync(cancellationToken);
        Requests.Add(new CapturedRequest(
            request.Method,
            request.RequestUri?.ToString() ?? "",
            request.Headers.ToDictionary(
                item => item.Key,
                item => string.Join(',', item.Value),
                StringComparer.OrdinalIgnoreCase
            ),
            request.Content?.Headers.ContentType?.MediaType,
            content
        ));
        return _responses.Dequeue()(request);
    }
}

internal sealed record CapturedRequest(
    HttpMethod Method,
    string Url,
    IReadOnlyDictionary<string, string> Headers,
    string? MediaType,
    byte[] Content
);
