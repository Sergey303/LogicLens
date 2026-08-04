using System.Text;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

internal static class DocxText
{
    private static readonly XNamespace Word =
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
    private static readonly Regex InlineWhitespace = new(
        "[ \\t]+",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking
    );

    public static string Paragraph(XElement paragraph)
    {
        var output = new StringBuilder();
        foreach (var element in paragraph.Descendants())
        {
            if (element.Name == Word + "t")
            {
                output.Append(element.Value);
            }
            else if (element.Name == Word + "tab")
            {
                output.Append('\t');
            }
            else if (element.Name == Word + "br" || element.Name == Word + "cr")
            {
                output.Append('\n');
            }
        }
        return output.ToString();
    }

    public static string TableCell(XElement cell)
    {
        return string.Join(
            '\n',
            cell.Elements(Word + "p")
                .Select(Paragraph)
                .Where(value => !string.IsNullOrWhiteSpace(value))
        );
    }

    public static string Normalize(string value)
    {
        var lines = value.Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n')
            .Split('\n')
            .Select(line => InlineWhitespace.Replace(line, " ").Trim())
            .Where(line => line.Length > 0);
        return string.Join('\n', lines);
    }
}
