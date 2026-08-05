using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfTestFixture
{
    public static byte[] PdfBytes => Encoding.ASCII.GetBytes("%PDF-1.7\nminimal-fixture\n%%EOF\n");

    public const string PdfInfo = """
        Pages:           2
        Page size:       612 x 792 pts (letter)
        """;

    public const string BboxXhtml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
          <body>
            <doc>
              <page width="612.000000" height="792.000000">
                <flow>
                  <block xMin="72" yMin="72" xMax="220" yMax="92">
                    <line xMin="72" yMin="72" xMax="220" yMax="92">
                      <word xMin="72" yMin="72" xMax="118" yMax="92">Evidence</word>
                      <word xMin="124" yMin="72" xMax="220" yMax="92">Heading</word>
                    </line>
                  </block>
                  <block xMin="72" yMin="110" xMax="420" yMax="150">
                    <line xMin="72" yMin="110" xMax="420" yMax="130">
                      <word xMin="72" yMin="110" xMax="120" yMax="130">First</word>
                      <word xMin="126" yMin="110" xMax="210" yMax="130">grounded</word>
                      <word xMin="216" yMin="110" xMax="300" yMax="130">paragraph.</word>
                    </line>
                  </block>
                </flow>
              </page>
              <page width="612.000000" height="792.000000">
                <flow>
                  <block xMin="72" yMin="72" xMax="400" yMax="96">
                    <line xMin="72" yMin="72" xMax="400" yMax="96">
                      <word xMin="72" yMin="72" xMax="140" yMax="96">Second</word>
                      <word xMin="146" yMin="72" xMax="210" yMax="96">page.</word>
                    </line>
                  </block>
                </flow>
              </page>
            </doc>
          </body>
        </html>
        """;
}
