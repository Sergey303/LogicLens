using System.Xml.Linq;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

internal static class DocxBodyParser
{
    private static readonly XNamespace Word =
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main";

    public static IReadOnlyList<DocxBlock> Parse(OoxmlPart documentPart)
    {
        var document = OoxmlXml.Parse(documentPart);
        var body = document.Root?.Element(Word + "body")
            ?? throw new InvalidDataException("DOCX document body is missing.");
        var blocks = new List<DocxBlock>();
        var state = new ParseState();
        foreach (var element in body.Elements())
        {
            state.BodyOrder++;
            if (element.Name == Word + "p")
            {
                AddParagraph(blocks, element, state);
                if (element.Element(Word + "pPr")?.Element(Word + "sectPr") is not null)
                {
                    state.SectionIndex++;
                }
            }
            else if (element.Name == Word + "tbl")
            {
                AddTable(blocks, element, state);
            }
        }
        if (blocks.Count == 0)
        {
            throw new InvalidDataException("DOCX contains no usable paragraph or table text.");
        }
        return blocks;
    }

    private static void AddParagraph(
        List<DocxBlock> blocks,
        XElement paragraph,
        ParseState state
    )
    {
        state.ParagraphIndex++;
        var raw = DocxText.Paragraph(paragraph);
        var normalized = DocxText.Normalize(raw);
        if (normalized.Length == 0)
        {
            return;
        }
        var anchor = new DocxSourceAnchor(
            state.SectionIndex,
            state.BodyOrder,
            state.ParagraphIndex,
            null,
            null,
            null
        );
        blocks.Add(CreateBlock("paragraph", raw, normalized, anchor));
    }

    private static void AddTable(
        List<DocxBlock> blocks,
        XElement table,
        ParseState state
    )
    {
        state.TableIndex++;
        var rowIndex = 0;
        foreach (var row in table.Elements(Word + "tr"))
        {
            rowIndex++;
            var columnIndex = 0;
            foreach (var cell in row.Elements(Word + "tc"))
            {
                columnIndex++;
                var raw = DocxText.TableCell(cell);
                var normalized = DocxText.Normalize(raw);
                if (normalized.Length == 0)
                {
                    continue;
                }
                var anchor = new DocxSourceAnchor(
                    state.SectionIndex,
                    state.BodyOrder,
                    null,
                    state.TableIndex,
                    rowIndex,
                    columnIndex
                );
                blocks.Add(CreateBlock("table-cell", raw, normalized, anchor));
            }
        }
    }

    private static DocxBlock CreateBlock(
        string kind,
        string raw,
        string normalized,
        DocxSourceAnchor anchor
    )
    {
        var contentHash = OoxmlHashing.Sha256(normalized);
        var identity = $"{kind}:{anchor}:{contentHash}";
        return new DocxBlock(
            $"docx:{OoxmlHashing.Sha256(identity)[..20]}",
            kind,
            raw,
            normalized,
            contentHash,
            anchor
        );
    }

    private sealed class ParseState
    {
        public int SectionIndex { get; set; } = 1;
        public int BodyOrder { get; set; }
        public int ParagraphIndex { get; set; }
        public int TableIndex { get; set; }
    }
}
