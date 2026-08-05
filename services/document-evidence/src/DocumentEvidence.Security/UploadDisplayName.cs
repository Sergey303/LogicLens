using System.Text;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public static class UploadDisplayName
{
    public static string Normalize(string value, int maxLength)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        if (maxLength < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(maxLength));
        }

        var normalizedPath = value.Replace('\\', '/');
        var baseName = normalizedPath.Split('/', StringSplitOptions.RemoveEmptyEntries).LastOrDefault();
        if (baseName is null)
        {
            throw new ArgumentException("Upload display name has no safe base name.", nameof(value));
        }

        var output = new StringBuilder(baseName.Length);
        var pendingSpace = false;
        foreach (var character in baseName.Trim())
        {
            if (char.IsControl(character))
            {
                throw new ArgumentException("Upload display name contains control characters.", nameof(value));
            }
            if (char.IsWhiteSpace(character))
            {
                pendingSpace = output.Length > 0;
                continue;
            }
            if (pendingSpace)
            {
                output.Append(' ');
                pendingSpace = false;
            }
            output.Append(character);
        }

        var result = output.ToString();
        if (result is "" or "." or ".." || result.Length > maxLength)
        {
            throw new ArgumentException(
                $"Upload display name must contain 1-{maxLength} safe characters.",
                nameof(value)
            );
        }
        return result;
    }
}
