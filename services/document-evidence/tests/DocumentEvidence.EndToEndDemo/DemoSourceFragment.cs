using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal static class DemoSourceFragment
{
    public static byte[] Export(UploadRevisionDto upload, DocumentFragmentDto fragment)
    {
        var value = fragment.Anchor.Value;
        var boundingBox = value.GetProperty("boundingBox");
        var block = new PdfBlock(
            value.GetProperty("blockId").GetString()
                ?? throw new InvalidDataException("PDF block ID is missing."),
            value.GetProperty("readingOrder").GetInt32(),
            fragment.Kind,
            fragment.Text,
            fragment.Text,
            fragment.ContentSha256,
            new PdfSourceAnchor(
                value.GetProperty("pageNumber").GetInt32(),
                value.GetProperty("blockOrdinal").GetInt32(),
                new PdfBoundingBox(
                    GetDouble(boundingBox, "XMin"),
                    GetDouble(boundingBox, "YMin"),
                    GetDouble(boundingBox, "XMax"),
                    GetDouble(boundingBox, "YMax")
                ),
                value.GetProperty("wordIds")
                    .EnumerateArray()
                    .Select(item => item.GetString() ?? string.Empty)
                    .ToArray()
            )
        );
        var sourceId = value.GetProperty("sourceId").GetString()
            ?? throw new InvalidDataException("PDF source ID is missing.");
        var artifactSha256 = value.GetProperty("artifactSha256").GetString()
            ?? throw new InvalidDataException("PDF artifact hash is missing.");
        var parserVersion = value.GetProperty("parserVersion").GetString()
            ?? throw new InvalidDataException("PDF parser version is missing.");
        return PdfSourceProposalBridge.ExportJsonLines(
            "document-evidence-pdf-v1",
            $"sha256:{upload.ManifestSha256}",
            new RetainedPdfEvidence(sourceId, artifactSha256, parserVersion, [block])
        );
    }

    private static double GetDouble(System.Text.Json.JsonElement value, string name)
    {
        return value.GetProperty(name).GetDouble();
    }
}
