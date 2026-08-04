using System.Globalization;
using System.Text.RegularExpressions;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

internal static class XlsxCellReference
{
    private static readonly Regex Reference = new(
        "^([A-Z]+)([1-9][0-9]*)$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );

    public static (int Row, int Column) Parse(string value)
    {
        var match = Reference.Match(value);
        if (!match.Success)
        {
            throw new InvalidDataException($"Invalid XLSX cell reference: {value}");
        }
        var column = 0;
        foreach (var character in match.Groups[1].Value)
        {
            column = checked(column * 26 + character - 'A' + 1);
        }
        var row = int.Parse(match.Groups[2].Value, CultureInfo.InvariantCulture);
        return (row, column);
    }
}
