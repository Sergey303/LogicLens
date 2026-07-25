using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;

namespace LogicLens.Ui.Validation;

public sealed class UiDocumentSchemaValidator : IDisposable
{
    private readonly JsonDocument schemaDocument;
    private readonly JsonSchema schema;
    private readonly UiDocumentValidationOptions options;

    public UiDocumentSchemaValidator(
        string schemaPath,
        UiDocumentValidationOptions? options = null)
    {
        if (string.IsNullOrWhiteSpace(schemaPath))
        {
            throw new ArgumentException(
                "Schema path cannot be null, empty, or whitespace.",
                nameof(schemaPath));
        }

        var absolutePath = Path.GetFullPath(schemaPath);
        schemaDocument = JsonDocument.Parse(File.ReadAllText(absolutePath));
        schema = JsonSchema.Build(
            schemaDocument.RootElement,
            new BuildOptions
            {
                Dialect = Dialect.Draft202012
            });
        this.options = options ?? new UiDocumentValidationOptions();
    }

    public IReadOnlyList<UiDocumentValidationError> Validate(JsonObject document)
    {
        ArgumentNullException.ThrowIfNull(document);

        using var instance = JsonDocument.Parse(document.ToJsonString());
        var results = schema.Evaluate(
            instance.RootElement,
            new EvaluationOptions
            {
                OutputFormat = OutputFormat.List
            });
        if (results.IsValid)
        {
            return [];
        }

        var errors = new List<UiDocumentValidationError>();
        CollectErrors(results, errors);
        return errors
            .OrderBy(static error => error.Path, StringComparer.Ordinal)
            .ThenBy(static error => error.Code, StringComparer.Ordinal)
            .ThenBy(static error => error.Message, StringComparer.Ordinal)
            .Take(options.MaxErrors)
            .ToArray();
    }

    public void Dispose() => schemaDocument.Dispose();

    private static void CollectErrors(
        EvaluationResults result,
        ICollection<UiDocumentValidationError> errors)
    {
        foreach (var pair in result.Errors.OrderBy(
                     static pair => pair.Key,
                     StringComparer.Ordinal))
        {
            errors.Add(new UiDocumentValidationError(
                "schema",
                result.InstanceLocation.ToString(),
                pair.Value));
        }

        foreach (var detail in result.Details)
        {
            CollectErrors(detail, errors);
        }
    }
}
