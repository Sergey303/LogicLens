using System.Text.Json.Nodes;
using LogicLens.Ui.Mapping;
using LogicLens.Ui.Validation;

namespace LogicLens.Ui;

public interface ISpecializedUiDocumentProvider
{
    ValueTask<JsonObject?> TryBuildEntityDocumentAsync(
        JsonObject entityViewResponse,
        JsonArray authoritativeFacts,
        string entityId,
        string language,
        CancellationToken cancellationToken);
}

public sealed class NullSpecializedUiDocumentProvider
    : ISpecializedUiDocumentProvider
{
    public ValueTask<JsonObject?> TryBuildEntityDocumentAsync(
        JsonObject entityViewResponse,
        JsonArray authoritativeFacts,
        string entityId,
        string language,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult<JsonObject?>(null);
}

public sealed class UiDocumentService(
    GenericUiDocumentMapper mapper,
    IUiDocumentValidator validator,
    ISpecializedUiDocumentProvider specializedProvider)
{
    public async ValueTask<JsonObject> BuildEntityDocumentAsync(
        JsonObject entityViewResponse,
        JsonArray authoritativeFacts,
        string entityId,
        string language,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(entityViewResponse);
        ArgumentNullException.ThrowIfNull(authoritativeFacts);
        ArgumentException.ThrowIfNullOrWhiteSpace(entityId);

        var specialized = await specializedProvider.TryBuildEntityDocumentAsync(
            entityViewResponse,
            authoritativeFacts,
            entityId,
            language,
            cancellationToken);
        if (specialized is not null)
        {
            var specializedResult = validator.Validate(
                specialized,
                authoritativeFacts,
                entityId);
            if (specializedResult.IsValid)
            {
                return specialized;
            }
        }

        var generic = mapper.MapEntityView(
            entityViewResponse,
            entityId,
            language);
        if (specialized is not null)
        {
            generic["diagnostics"]!.AsArray().Add(
                GenericUiDocumentMapper.CreateDiagnostic(
                    "specialized_view_fallback",
                    "warning",
                    "Специализированное представление отклонено; показано универсальное."));
        }

        var genericResult = validator.Validate(
            generic,
            authoritativeFacts,
            entityId);
        if (!genericResult.IsValid)
        {
            throw new UiDocumentContractException(genericResult.Errors);
        }

        return generic;
    }
}
