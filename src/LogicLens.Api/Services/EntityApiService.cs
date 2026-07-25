using System.Text.Json.Nodes;
using LogicLens.Api.Runtime;
using LogicLens.Ui;

namespace LogicLens.Api.Services;

public sealed class EntityApiService(
    IPrologCliClient prolog,
    UiDocumentService uiDocuments)
{
    public async Task<JsonObject> GetHealthAsync(
        CancellationToken cancellationToken)
    {
        var response = await prolog.ExecuteAsync(
            "health",
            new JsonObject(),
            cancellationToken);
        return RequiredObject(response, "result");
    }

    public async Task<JsonObject> GetFactsAsync(
        string entityId,
        CancellationToken cancellationToken)
    {
        ValidateEntityId(entityId);
        var response = await prolog.ExecuteAsync(
            "inspect-facts",
            new JsonObject
            {
                ["entityId"] = entityId
            },
            cancellationToken);
        return RequiredObject(response, "result");
    }

    public async Task<string> GetPrologAsync(
        string entityId,
        CancellationToken cancellationToken)
    {
        ValidateEntityId(entityId);
        var response = await GetEntityViewResponseAsync(
            entityId,
            "ru",
            includeRawProlog: true,
            cancellationToken);
        var result = RequiredObject(response, "result");
        return result["rawProlog"]?.GetValue<string?>()
            ?? string.Empty;
    }

    public async Task<JsonObject> GetViewAsync(
        string entityId,
        string language,
        bool includeRawProlog,
        CancellationToken cancellationToken)
    {
        ValidateEntityId(entityId);
        ValidateLanguage(language);

        var viewTask = GetEntityViewResponseAsync(
            entityId,
            language,
            includeRawProlog,
            cancellationToken);
        var factsTask = GetFactsResponseAsync(entityId, cancellationToken);
        await Task.WhenAll(viewTask, factsTask);

        var viewResponse = await viewTask;
        var factsResponse = await factsTask;
        var facts = RequiredArray(
            RequiredObject(factsResponse, "result"),
            "facts");
        return await uiDocuments.BuildEntityDocumentAsync(
            viewResponse,
            facts,
            entityId,
            language,
            cancellationToken);
    }

    private Task<JsonObject> GetEntityViewResponseAsync(
        string entityId,
        string language,
        bool includeRawProlog,
        CancellationToken cancellationToken) =>
        prolog.ExecuteAsync(
            "entity-view",
            new JsonObject
            {
                ["entityId"] = entityId,
                ["language"] = language,
                ["includeRawProlog"] = includeRawProlog
            },
            cancellationToken);

    private Task<JsonObject> GetFactsResponseAsync(
        string entityId,
        CancellationToken cancellationToken) =>
        prolog.ExecuteAsync(
            "inspect-facts",
            new JsonObject
            {
                ["entityId"] = entityId
            },
            cancellationToken);

    private static void ValidateEntityId(string entityId)
    {
        if (string.IsNullOrWhiteSpace(entityId) || entityId.Length > 1024)
        {
            throw new ArgumentException(
                "Entity identifier must contain 1 to 1024 characters.",
                nameof(entityId));
        }
    }

    private static void ValidateLanguage(string language)
    {
        if (string.IsNullOrWhiteSpace(language) || language.Length > 64)
        {
            throw new ArgumentException(
                "Language must contain 1 to 64 characters.",
                nameof(language));
        }
    }

    private static JsonObject RequiredObject(JsonObject parent, string name) =>
        parent[name] as JsonObject
        ?? throw new PrologCliException(
            "invalid_response",
            $"The Prolog runtime response is missing object '{name}'.");

    private static JsonArray RequiredArray(JsonObject parent, string name) =>
        parent[name] as JsonArray
        ?? throw new PrologCliException(
            "invalid_response",
            $"The Prolog runtime response is missing array '{name}'.");
}
