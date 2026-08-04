using System.Globalization;
using System.Text.RegularExpressions;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal static partial class PdfInfoParser
{
    public static PdfInfo Parse(string output)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(output);
        var pages = ParseInt(output, "Pages");
        if (pages < 1)
        {
            throw new InvalidDataException("pdfinfo reported no pages.");
        }

        var match = PageSizeRegex().Match(output);
        if (!match.Success)
        {
            throw new InvalidDataException("pdfinfo did not report a page size.");
        }
        return new PdfInfo(
            pages,
            double.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture),
            double.Parse(match.Groups[2].Value, CultureInfo.InvariantCulture)
        );
    }

    private static int ParseInt(string output, string field)
    {
        var match = Regex.Match(
            output,
            $"^{Regex.Escape(field)}:\\s*(\\d+)\\s*$",
            RegexOptions.Multiline | RegexOptions.CultureInvariant
        );
        if (!match.Success)
        {
            throw new InvalidDataException($"pdfinfo did not report {field}.");
        }
        return int.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
    }

    [GeneratedRegex(
        @"^Page size:\s*([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        RegexOptions.Multiline | RegexOptions.CultureInvariant
    )]
    private static partial Regex PageSizeRegex();
}

internal sealed record PdfInfo(int PageCount, double Width, double Height);
