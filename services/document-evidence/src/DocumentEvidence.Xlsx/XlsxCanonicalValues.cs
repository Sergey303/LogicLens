using System.Globalization;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

internal static class XlsxCanonicalValues
{
    public static string? Boolean(string? value) => value switch
    {
        "0" => "false",
        "1" => "true",
        null => null,
        _ => throw new InvalidDataException($"Invalid XLSX boolean value: {value}"),
    };

    public static string? Date(string? value)
    {
        if (value is null)
        {
            return null;
        }
        if (!DateTimeOffset.TryParse(
            value,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AllowWhiteSpaces | DateTimeStyles.AssumeUniversal,
            out var parsed
        ))
        {
            throw new InvalidDataException($"Invalid XLSX date value: {value}");
        }
        return parsed.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture);
    }
}
