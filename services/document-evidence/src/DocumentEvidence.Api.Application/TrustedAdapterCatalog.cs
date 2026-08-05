using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Application;

internal sealed record TrustedAdapterDescriptor(string Name, string Version);

internal static class TrustedAdapterCatalog
{
    public static TrustedAdapterDescriptor Resolve(string mediaType) => mediaType switch
    {
        UploadMediaSignature.Pdf => new("poppler", "24.02.0"),
        UploadMediaSignature.Docx => new("docx-ooxml", "1.0.0"),
        UploadMediaSignature.Xlsx => new("xlsx-ooxml", "1.0.0"),
        _ => throw new InvalidDataException($"Unsupported trusted media type: {mediaType}"),
    };
}
