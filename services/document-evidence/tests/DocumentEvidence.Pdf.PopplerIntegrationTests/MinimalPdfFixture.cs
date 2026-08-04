using System.Globalization;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.PopplerIntegrationTests;

internal static class MinimalPdfFixture
{
    public static byte[] Create()
    {
        const string content = """
            BT
            /F1 18 Tf
            72 720 Td
            (Evidence Heading) Tj
            /F1 12 Tf
            0 -36 Td
            (First grounded paragraph.) Tj
            ET
            """;
        var contentLength = Encoding.ASCII.GetByteCount(content);
        var objects = new[]
        {
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
                "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            $"<< /Length {contentLength} >>\nstream\n{content}endstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        };

        using var stream = new MemoryStream();
        Write(stream, "%PDF-1.4\n");
        var offsets = new List<long>();
        for (var index = 0; index < objects.Length; index++)
        {
            offsets.Add(stream.Position);
            Write(stream, $"{index + 1} 0 obj\n{objects[index]}\nendobj\n");
        }

        var xrefOffset = stream.Position;
        Write(stream, $"xref\n0 {objects.Length + 1}\n");
        Write(stream, "0000000000 65535 f \n");
        foreach (var offset in offsets)
        {
            Write(stream, offset.ToString("0000000000", CultureInfo.InvariantCulture) + " 00000 n \n");
        }
        Write(
            stream,
            $"trailer\n<< /Size {objects.Length + 1} /Root 1 0 R >>\n" +
            $"startxref\n{xrefOffset}\n%%EOF\n"
        );
        return stream.ToArray();
    }

    private static void Write(Stream stream, string value)
    {
        stream.Write(Encoding.ASCII.GetBytes(value));
    }
}
