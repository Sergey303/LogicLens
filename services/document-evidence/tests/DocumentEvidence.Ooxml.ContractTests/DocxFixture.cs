namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class DocxFixture
{
    public static byte[] Build(bool reverse = false, DateTimeOffset? timestamp = null) =>
        OoxmlTestZip.Build(Parts, reverse, timestamp);

    private static readonly IReadOnlyList<(string Name, string Content)> Parts =
    [
        ("[Content_Types].xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
              <Override PartName="/word/document.xml"
                ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml" />
              <Override PartName="/docProps/core.xml"
                ContentType="application/vnd.openxmlformats-package.core-properties+xml" />
            </Types>
            """),
        ("_rels/.rels", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                Target="word/document.xml" />
            </Relationships>
            """),
        ("docProps/core.xml", OoxmlTestZip.CoreProperties),
        ("word/document.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:r><w:t>First   paragraph</w:t></w:r></w:p>
                <w:p>
                  <w:pPr><w:sectPr /></w:pPr>
                  <w:r><w:t>Section break</w:t></w:r>
                </w:p>
                <w:tbl>
                  <w:tr>
                    <w:tc><w:p><w:r><w:t>Cell A</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:t>Cell B</w:t></w:r></w:p></w:tc>
                  </w:tr>
                </w:tbl>
                <w:sectPr />
              </w:body>
            </w:document>
            """),
    ];
}
