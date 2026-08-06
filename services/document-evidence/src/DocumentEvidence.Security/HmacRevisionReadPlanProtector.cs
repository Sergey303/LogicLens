using System.Security.Cryptography;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public sealed class HmacRevisionReadPlanProtector : IRevisionReadPlanProtector
{
    private const int MinimumKeyBytes = 32;
    private const int MaximumTokenLength = 4096;
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly byte[] _key;

    public HmacRevisionReadPlanProtector(byte[] key)
    {
        ArgumentNullException.ThrowIfNull(key);
        if (key.Length < MinimumKeyBytes)
        {
            throw new ArgumentException("Read plan signing key must contain at least 32 bytes.",
                nameof(key));
        }
        _key = key.ToArray();
    }

    public string Protect(RevisionReadPlanPayload payload)
    {
        ArgumentNullException.ThrowIfNull(payload);
        ValidatePayload(payload);
        var body = JsonSerializer.SerializeToUtf8Bytes(payload, JsonOptions);
        var signature = HMACSHA256.HashData(_key, body);
        return $"{Encode(body)}.{Encode(signature)}";
    }

    public RevisionReadPlanPayload Unprotect(string token)
    {
        if (String.IsNullOrWhiteSpace(token) || token.Length > MaximumTokenLength)
        {
            throw InvalidToken();
        }
        try
        {
            var segments = token.Split('.');
            if (segments.Length != 2)
            {
                throw new FormatException("Read plan token must have two segments.");
            }
            var body = Decode(segments[0]);
            var signature = Decode(segments[1]);
            var expected = HMACSHA256.HashData(_key, body);
            if (signature.Length != expected.Length ||
                !CryptographicOperations.FixedTimeEquals(signature, expected))
            {
                throw new CryptographicException("Read plan signature mismatch.");
            }
            var payload = JsonSerializer.Deserialize<RevisionReadPlanPayload>(body, JsonOptions)
                ?? throw new JsonException("Read plan payload is missing.");
            ValidatePayload(payload);
            return payload;
        }
        catch (Exception error) when (error is FormatException or JsonException or
            CryptographicException or InvalidDataException)
        {
            throw InvalidToken(error);
        }
    }

    private static void ValidatePayload(RevisionReadPlanPayload payload)
    {
        if (payload.Version != 1 || payload.PlanId == Guid.Empty ||
            payload.ActorId == Guid.Empty || payload.WorkspaceId == Guid.Empty ||
            payload.DocumentId == Guid.Empty || payload.RevisionId == Guid.Empty ||
            payload.RevisionNumber <= 0 || payload.ObjectSha256.Length != 64 ||
            payload.SizeBytes < 0 || String.IsNullOrWhiteSpace(payload.MediaType) ||
            payload.IssuedAtUtc >= payload.ExpiresAtUtc)
        {
            throw new InvalidDataException("Read plan payload is invalid.");
        }
    }

    private static string Encode(byte[] value)
    {
        return Convert.ToBase64String(value)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
    }

    private static byte[] Decode(string value)
    {
        var normalized = value.Replace('-', '+').Replace('_', '/');
        normalized = normalized.Length % 4 switch
        {
            0 => normalized,
            2 => normalized + "==",
            3 => normalized + "=",
            _ => throw new FormatException("Invalid base64url length.")
        };
        return Convert.FromBase64String(normalized);
    }

    private static UnauthorizedAccessException InvalidToken(Exception? inner = null)
    {
        return new UnauthorizedAccessException("Revision read plan token is invalid.", inner);
    }
}
