using System.Text.Json.Nodes;
using LogicLens.Api.Runtime;
using LogicLens.Api.Services;
using LogicLens.Ui;
using LogicLens.Ui.Mapping;
using LogicLens.Ui.Validation;
using Microsoft.AspNetCore.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

var prologOptions = builder.Configuration
    .GetSection("Prolog")
    .Get<PrologCliOptions>() ?? new PrologCliOptions();
if (!Path.IsPathRooted(prologOptions.EpochPath))
{
    prologOptions = prologOptions with
    {
        EpochPath = Path.GetFullPath(Path.Combine(
            builder.Environment.ContentRootPath,
            prologOptions.EpochPath))
    };
}

var validationOptions = builder.Configuration
    .GetSection("UiDocument:Limits")
    .Get<UiDocumentValidationOptions>() ?? new UiDocumentValidationOptions();
var configuredSchemaPath = builder.Configuration["UiDocument:SchemaPath"];
var schemaPath = string.IsNullOrWhiteSpace(configuredSchemaPath)
    ? Path.Combine(
        AppContext.BaseDirectory,
        "contracts",
        "ui-document-v0.schema.json")
    : Path.GetFullPath(
        Path.IsPathRooted(configuredSchemaPath)
            ? configuredSchemaPath
            : Path.Combine(
                builder.Environment.ContentRootPath,
                configuredSchemaPath));

builder.Services.AddSingleton(prologOptions);
builder.Services.AddSingleton<PrologCliClient>();
builder.Services.AddSingleton<IPrologCliClient>(services =>
    new StateCheckingPrologCliClient(
        services.GetRequiredService<PrologCliClient>(),
        prologOptions));
builder.Services.AddSingleton(validationOptions);
builder.Services.AddSingleton<IUiDocumentValidator>(_ =>
    new UiDocumentValidator(schemaPath, validationOptions));
builder.Services.AddSingleton<GenericUiDocumentMapper>();
builder.Services.AddSingleton<
    ISpecializedUiDocumentProvider,
    NullSpecializedUiDocumentProvider>();
builder.Services.AddSingleton<UiDocumentService>();
builder.Services.AddSingleton<EntityApiService>();

var app = builder.Build();

app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        var feature = context.Features.Get<IExceptionHandlerFeature>();
        var exception = feature?.Error;
        var (status, code, title) = exception switch
        {
            ArgumentException => (
                StatusCodes.Status400BadRequest,
                "invalid_request",
                "The API request is invalid."),
            PrologCliException { Code: "timeout" } => (
                StatusCodes.Status504GatewayTimeout,
                "prolog_timeout",
                "The logical runtime timed out."),
            PrologCliException prolog => (
                StatusCodes.Status502BadGateway,
                "prolog_" + prolog.Code,
                "The logical runtime rejected the request."),
            UiDocumentContractException => (
                StatusCodes.Status502BadGateway,
                "ui_document_invalid",
                "The generated UI Document was rejected."),
            OperationCanceledException => (
                499,
                "request_cancelled",
                "The request was cancelled."),
            _ => (
                StatusCodes.Status500InternalServerError,
                "internal_error",
                "The API could not complete the request.")
        };

        var problem = new JsonObject
        {
            ["type"] = "https://logiclens.local/problems/" + code,
            ["title"] = title,
            ["status"] = status,
            ["code"] = code,
            ["traceId"] = context.TraceIdentifier
        };
        if (exception is ArgumentException argument)
        {
            problem["detail"] = argument.Message;
        }
        else if (exception is PrologCliException prolog)
        {
            problem["detail"] = prolog.Message;
        }
        else if (exception is UiDocumentContractException contract)
        {
            problem["errors"] = new JsonArray(
                contract.Errors
                    .Take(20)
                    .Select(error => (JsonNode)new JsonObject
                    {
                        ["code"] = error.Code,
                        ["path"] = error.Path,
                        ["message"] = error.Message
                    })
                    .ToArray());
        }

        context.Response.StatusCode = status;
        context.Response.ContentType = "application/problem+json";
        await context.Response.WriteAsJsonAsync(
            problem,
            cancellationToken: context.RequestAborted);
    });
});

app.MapGet(
    "/api/health",
    async (EntityApiService service, CancellationToken cancellationToken) =>
        Results.Json(await service.GetHealthAsync(cancellationToken)));

app.MapGet(
    "/api/entities/{id}/facts",
    async (
        string id,
        EntityApiService service,
        CancellationToken cancellationToken) =>
        Results.Json(await service.GetFactsAsync(id, cancellationToken)));

app.MapGet(
    "/api/entities/{id}/prolog",
    async (
        string id,
        EntityApiService service,
        CancellationToken cancellationToken) =>
        Results.Text(
            await service.GetPrologAsync(id, cancellationToken),
            "text/plain",
            System.Text.Encoding.UTF8));

app.MapGet(
    "/api/entities/{id}/view",
    async (
        string id,
        string? language,
        bool? includeProlog,
        EntityApiService service,
        CancellationToken cancellationToken) =>
    {
        var effectiveLanguage = string.IsNullOrWhiteSpace(language)
            ? "ru"
            : language.ToLowerInvariant();
        var document = await service.GetViewAsync(
            id,
            effectiveLanguage,
            includeProlog ?? true,
            cancellationToken);
        return Results.Json(document);
    });

app.Run();

public partial class Program
{
}
