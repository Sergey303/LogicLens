using System.IO.Compression;
using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class OoxmlZipMutation
{
    public static byte[] Replace(byte[] package, string partName, string content)
    {
        using var stream = new MemoryStream();
        stream.Write(package, 0, package.Length);
        stream.Position = 0;
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Update, leaveOpen: true))
        {
            var existing = archive.GetEntry(partName)
                ?? throw new InvalidOperationException($"Fixture part is missing: {partName}");
            existing.Delete();
            var replacement = archive.CreateEntry(partName, CompressionLevel.Optimal);
            replacement.LastWriteTime = new DateTimeOffset(
                2026,
                8,
                4,
                0,
                0,
                0,
                TimeSpan.Zero
            );
            using var writer = new StreamWriter(
                replacement.Open(),
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)
            );
            writer.Write(content);
        }
        return stream.ToArray();
    }
}
