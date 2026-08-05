using System.IO.Compression;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class OoxmlTestZip
{
    public static byte[] Build(
        IReadOnlyList<(string Name, string Content)> parts,
        bool reverse = false,
        DateTimeOffset? timestamp = null
    )
    {
        using var output = new MemoryStream();
        using (var archive = new ZipArchive(output, ZipArchiveMode.Create, leaveOpen: true))
        {
            var ordered = reverse ? parts.Reverse() : parts;
            foreach (var (name, content) in ordered)
            {
                var entry = archive.CreateEntry(name, CompressionLevel.Optimal);
                entry.LastWriteTime = timestamp ?? new DateTimeOffset(2020, 1, 1, 0, 0, 0, TimeSpan.Zero);
                using var stream = entry.Open();
                var bytes = Encoding.UTF8.GetBytes(content);
                stream.Write(bytes, 0, bytes.Length);
            }
        }
        return output.ToArray();
    }

    public static string CoreProperties => """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <cp:coreProperties
          xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
          xmlns:dc="http://purl.org/dc/elements/1.1/"
          xmlns:dcterms="http://purl.org/dc/terms/"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <dc:title>  Contract   fixture </dc:title>
          <dc:creator>KnowledgePilot</dc:creator>
          <dcterms:created xsi:type="dcterms:W3CDTF">2026-08-04T15:00:00+03:00</dcterms:created>
          <dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-04T15:01:00+03:00</dcterms:modified>
        </cp:coreProperties>
        """;
}
