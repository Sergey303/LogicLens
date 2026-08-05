namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public static class UploadMediaSignature
{
    public const string Pdf = "application/pdf";
    public const string Docx =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    public const string Xlsx =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

    public static void DemandMatch(string mediaType, ReadOnlySpan<byte> content)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(mediaType);
        var matches = mediaType switch
        {
            Pdf => content.StartsWith("%PDF-"u8),
            Docx or Xlsx => IsZip(content),
            _ => throw new InvalidDataException($"Unsupported trusted upload media type: {mediaType}"),
        };
        if (!matches)
        {
            throw new InvalidDataException(
                $"Upload signature does not match declared media type: {mediaType}"
            );
        }
    }

    private static bool IsZip(ReadOnlySpan<byte> content)
    {
        return content.Length >= 4
            && content[0] == (byte)'P'
            && content[1] == (byte)'K'
            && content[2] == 3
            && content[3] == 4;
    }
}
