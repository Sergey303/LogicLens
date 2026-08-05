using System.Globalization;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal static class DemoPdfFixture
{
    public const string Quote =
        "The Product Owner is accountable for maximizing the value of the product.";

    public static byte[] Create()
    {
        var content = $"""
            BT
            /F1 18 Tf
            72 720 Td
            (Product accountability) Tj
            /F1 12 Tf
            0 -36 Td
            ({Quote}) Tj
            ET
            """;
        var objects = Objects(content);
        using var stream = new MemoryStream();
        Write(stream, "%PDF-1.4\n");
        var offsets = new List<long>();
        for (var index = 0; index < objects.Length; index++)
        {
            offsets.Add(stream.Position);
            Write(stream, $"{index + 1} 0 obj\n{objects[index]}\nendobj\n");
        }
        var xrefOffset = stream.Position;
        Write(stream, $"xref\n0 {objects.Length + 1}\n0000000000 65535 f \n");
        foreach (var offset in offsets)
        {
            Write(stream, offset.ToString("0000000000", CultureInfo.InvariantCulture));
            Write(stream, " 00000 n \n");
        }
        Write(
            stream,
            $"trailer\n<< /Size {objects.Length + 1} /Root 1 0 R >>\n" +
            $"startxref\n{xrefOffset}\n%%EOF\n"
        );
        return stream.ToArray();
    }

    private static string[] Objects(string content)
    {
        var length = Encoding.ASCII.GetByteCount(content);
        return
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
                "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            $"<< /Length {length} >>\nstream\n{content}endstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ];
    }

    private static void Write(Stream stream, string value)
    {
        stream.Write(Encoding.ASCII.GetBytes(value));
    }
}
