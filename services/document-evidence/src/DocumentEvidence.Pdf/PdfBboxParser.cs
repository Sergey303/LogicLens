using System.Globalization;
using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

internal static class PdfBboxParser
{
    public static IReadOnlyList<PdfRawPage> Parse(string xhtml)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(xhtml);
        XDocument document;
        try
        {
            document = XDocument.Parse(xhtml, LoadOptions.PreserveWhitespace);
        }
        catch (Exception exception) when (exception is System.Xml.XmlException or ArgumentException)
        {
            throw new InvalidDataException("Poppler bbox output is not valid XML.", exception);
        }

        var pageElements = document.Descendants().Where(element => element.Name.LocalName == "page").ToList();
        if (pageElements.Count == 0)
        {
            throw new InvalidDataException("Poppler bbox output contains no pages.");
        }

        return pageElements.Select((page, index) => ParsePage(page, index + 1)).ToList();
    }

    private static PdfRawPage ParsePage(XElement page, int pageNumber)
    {
        var width = ParseCoordinate(page, "width");
        var height = ParseCoordinate(page, "height");
        var blocks = page.Descendants()
            .Where(element => element.Name.LocalName == "block")
            .Select((block, index) => ParseBlock(block, pageNumber, index + 1))
            .Where(block => block is not null)
            .Cast<PdfRawBlock>()
            .ToList();
        return new PdfRawPage(pageNumber, width, height, blocks);
    }

    private static PdfRawBlock? ParseBlock(XElement block, int pageNumber, int blockOrdinal)
    {
        var wordOrdinal = 0;
        var wordIds = new List<string>();
        var lines = new List<string>();
        foreach (var line in block.Descendants().Where(element => element.Name.LocalName == "line"))
        {
            var words = line.Descendants()
                .Where(element => element.Name.LocalName == "word")
                .Select(word => NormalizeWord(word.Value))
                .Where(word => word.Length > 0)
                .ToList();
            if (words.Count == 0)
            {
                continue;
            }
            foreach (var _ in words)
            {
                wordOrdinal++;
                wordIds.Add($"p{pageNumber:0000}:b{blockOrdinal:0000}:w{wordOrdinal:0000}");
            }
            lines.Add(string.Join(' ', words));
        }

        var text = string.Join('\n', lines).Trim();
        if (text.Length == 0)
        {
            return null;
        }
        return new PdfRawBlock(
            blockOrdinal,
            text,
            NormalizeText(text),
            ParseBox(block),
            wordIds
        );
    }

    private static PdfBoundingBox ParseBox(XElement element)
    {
        var box = new PdfBoundingBox(
            ParseCoordinate(element, "xMin"),
            ParseCoordinate(element, "yMin"),
            ParseCoordinate(element, "xMax"),
            ParseCoordinate(element, "yMax")
        );
        if (box.XMin < 0 || box.YMin < 0 || box.XMax < box.XMin || box.YMax < box.YMin)
        {
            throw new InvalidDataException("Poppler returned an invalid bounding box.");
        }
        return box;
    }

    private static double ParseCoordinate(XElement element, string attributeName)
    {
        var value = element.Attribute(attributeName)?.Value;
        if (!double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var result) ||
            !double.IsFinite(result))
        {
            throw new InvalidDataException($"Poppler bbox attribute '{attributeName}' is invalid.");
        }
        return result;
    }

    private static string NormalizeWord(string value)
    {
        return string.Join(' ', value.Replace('\u00a0', ' ').Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));
    }

    private static string NormalizeText(string value)
    {
        return string.Join('\n', value.Split('\n').Select(NormalizeWord).Where(line => line.Length > 0));
    }
}
