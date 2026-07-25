using System.Text.Json.Nodes;

namespace LogicLens.Ui.Validation;

public sealed class UiDocumentValidator : IUiDocumentValidator, IDisposable
{
    private readonly UiDocumentSchemaValidator schemaValidator;
    private readonly UiDocumentSemanticValidator semanticValidator;

    public UiDocumentValidator(
        string schemaPath,
        UiDocumentValidationOptions? options = null)
    {
        var effectiveOptions = options ?? new UiDocumentValidationOptions();
        schemaValidator = new UiDocumentSchemaValidator(schemaPath, effectiveOptions);
        semanticValidator = new UiDocumentSemanticValidator(effectiveOptions);
    }

    public UiDocumentValidationResult Validate(
        JsonObject document,
        JsonArray authoritativeFacts,
        string rootEntityId)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(authoritativeFacts);
        ArgumentException.ThrowIfNullOrWhiteSpace(rootEntityId);

        var schemaErrors = schemaValidator.Validate(document);
        if (schemaErrors.Count > 0)
        {
            return new UiDocumentValidationResult(schemaErrors);
        }

        try
        {
            var semanticErrors = semanticValidator.Validate(
                document,
                authoritativeFacts,
                rootEntityId);
            return semanticErrors.Count == 0
                ? UiDocumentValidationResult.Success
                : new UiDocumentValidationResult(semanticErrors);
        }
        catch (InvalidDataException exception)
        {
            return new UiDocumentValidationResult(
            [
                new UiDocumentValidationError(
                    "authoritative_data",
                    "",
                    exception.Message)
            ]);
        }
    }

    public void Dispose() => schemaValidator.Dispose();
}
