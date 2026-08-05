using System.Text.RegularExpressions;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal static class PdfToolOutput
{
    private static readonly Regex VersionRegex = new(
        @"version\s+([^\s]+)",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant | RegexOptions.Compiled
    );

    public static string DemandSuccess(PdfProcessResult result, string tool)
    {
        if (result.ExitCode != 0)
        {
            var detail = string.IsNullOrWhiteSpace(result.StandardError)
                ? result.StandardOutput
                : result.StandardError;
            detail = detail.Trim();
            if (detail.Length > 2000)
            {
                detail = detail[^2000..];
            }
            throw new InvalidDataException($"{tool} failed: {detail}");
        }
        return result.StandardOutput;
    }

    public static string ParseVersion(PdfProcessResult result)
    {
        _ = DemandSuccess(result, "pdftotext -v");
        var output = string.IsNullOrWhiteSpace(result.StandardError)
            ? result.StandardOutput
            : result.StandardError;
        var match = VersionRegex.Match(output);
        return match.Success ? match.Groups[1].Value : "unknown";
    }
}
