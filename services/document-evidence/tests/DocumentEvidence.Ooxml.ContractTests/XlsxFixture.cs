namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class XlsxFixture
{
    public static byte[] Build(bool reverse = false, DateTimeOffset? timestamp = null) =>
        OoxmlTestZip.Build(Parts, reverse, timestamp);

    private static readonly IReadOnlyList<(string Name, string Content)> Parts =
    [
        ("[Content_Types].xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
              <Override PartName="/xl/workbook.xml"
                ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml" />
              <Override PartName="/xl/worksheets/sheet1.xml"
                ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml" />
              <Override PartName="/xl/worksheets/sheet2.xml"
                ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml" />
              <Override PartName="/xl/sharedStrings.xml"
                ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml" />
              <Override PartName="/docProps/core.xml"
                ContentType="application/vnd.openxmlformats-package.core-properties+xml" />
            </Types>
            """),
        ("_rels/.rels", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                Target="xl/workbook.xml" />
            </Relationships>
            """),
        ("docProps/core.xml", OoxmlTestZip.CoreProperties),
        ("xl/workbook.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
              <sheets>
                <sheet name="Input" sheetId="1" r:id="rId1" />
                <sheet name="Flags" sheetId="2" r:id="rId2" />
              </sheets>
            </workbook>
            """),
        ("xl/_rels/workbook.xml.rels", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet1.xml" />
              <Relationship Id="rId2"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet2.xml" />
              <Relationship Id="rId3"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
                Target="sharedStrings.xml" />
            </Relationships>
            """),
        ("xl/sharedStrings.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <si><t>Shared value</t></si>
            </sst>
            """),
        ("xl/worksheets/sheet1.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData>
                <row r="1">
                  <c r="A1" t="s"><v>0</v></c>
                  <c r="B1"><f>SUM(1,2)</f><v>3</v></c>
                </row>
                <row r="2">
                  <c r="C2" t="inlineStr"><is><t>Inline value</t></is></c>
                  <c r="D2" t="d"><v>2026-08-04T15:00:00+03:00</v></c>
                </row>
              </sheetData>
            </worksheet>
            """),
        ("xl/worksheets/sheet2.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData><row r="1"><c r="A1" t="b"><v>1</v></c></row></sheetData>
            </worksheet>
            """),
    ];
}
