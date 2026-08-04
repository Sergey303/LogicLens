using KnowledgePilot.LogicLens.DocumentEvidence.Docx;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class DocxContractTests
{
    public static async Task ParagraphSectionAndTableAnchorsAreStableAsync()
    {
        var adapter = new DocxAdapter();
        var first = await ExtractAsync(adapter, DocxFixture.Build(reverse: false));
        var second = await ExtractAsync(adapter, DocxFixture.Build(
            reverse: true,
            timestamp: new DateTimeOffset(2025, 2, 2, 0, 0, 0, TimeSpan.Zero)
        ));

        TestAssert.Equal(first.IrSha256, second.IrSha256, "DOCX IR must be deterministic.");
        TestAssert.Equal(
            first.PackageEntriesSha256,
            second.PackageEntriesSha256,
            "DOCX semantic package identity must be deterministic."
        );
        TestAssert.True(
            first.ArtifactSha256 != second.ArtifactSha256,
            "DOCX raw artifact identity must preserve ZIP-level differences."
        );
        TestAssert.Equal(4, first.Blocks.Count, "DOCX fixture must expose four text blocks.");
        TestAssert.Equal(
            "First paragraph",
            first.Blocks[0].NormalizedText,
            "DOCX paragraph whitespace must be normalized."
        );
        TestAssert.Equal(1, first.Blocks[0].Anchor.SectionIndex, "First paragraph section is wrong.");
        TestAssert.Equal(2, first.Blocks[2].Anchor.SectionIndex, "Table must follow section break.");
        TestAssert.Equal(1, first.Blocks[2].Anchor.TableIndex, "Table anchor is missing.");
        TestAssert.Equal(1, first.Blocks[2].Anchor.RowIndex, "Table row anchor is missing.");
        TestAssert.Equal(1, first.Blocks[2].Anchor.ColumnIndex, "Table column anchor is missing.");
    }

    public static async Task MissingMainDocumentFailsClosedAsync()
    {
        var package = OoxmlTestZip.Build([
            ("[Content_Types].xml", """
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                  <Override PartName="/word/document.xml"
                    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml" />
                </Types>
                """),
            ("_rels/.rels", """
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                  <Relationship Id="rId1"
                    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                    Target="word/document.xml" />
                </Relationships>
                """),
        ]);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ExtractAsync(new DocxAdapter(), package),
            "DOCX without its declared main document part must fail closed."
        );
    }

    private static Task<DocxDocument> ExtractAsync(DocxAdapter adapter, byte[] content) =>
        adapter.ExtractAsync(new MemoryStream(content, writable: false));
}
