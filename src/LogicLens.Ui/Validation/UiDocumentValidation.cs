using System.Text.Json.Nodes;

namespace LogicLens.Ui.Validation;

public sealed record UiDocumentValidationOptions
{
    public int MaxSectionDepth { get; init; } = 8;

    public int MaxComponents { get; init; } = 5_000;

    public int MaxValues { get; init; } = 20_000;

    public int MaxDocumentBytes { get; init; } = 2_000_000;

    public int MaxErrors { get; init; } = 100;
}

public sealed record UiDocumentValidationError(
    string Code,
    string Path,
    string Message);

public sealed record UiDocumentValidationResult(
    IReadOnlyList<UiDocumentValidationError> Errors)
{
    public bool IsValid => Errors.Count == 0;

    public static UiDocumentValidationResult Success { get; } = new([]);
}

public sealed class UiDocumentContractException(
    IReadOnlyList<UiDocumentValidationError> errors)
    : Exception("UI Document validation failed.")
{
    public IReadOnlyList<UiDocumentValidationError> Errors { get; } = errors;
}

public interface IUiDocumentValidator
{
    UiDocumentValidationResult Validate(
        JsonObject document,
        JsonArray authoritativeFacts,
        string rootEntityId);
}
