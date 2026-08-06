using System.Text;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal static class HmacReadPlanProtectorContractTests
{
    public static void RoundTripPreservesPayloadWithoutStoragePath()
    {
        var protector = CreateProtector(1);
        var payload = CreatePayload();
        var token = protector.Protect(payload);
        var restored = protector.Unprotect(token);
        Assert(restored == payload, "Signed read plan must round-trip exactly.");
        var json = Encoding.UTF8.GetString(Decode(token.Split('.')[0]));
        Assert(!json.Contains("path", StringComparison.OrdinalIgnoreCase),
            "Signed plan payload must not reveal a storage path.");
        Assert(!json.Contains("storageKey", StringComparison.OrdinalIgnoreCase),
            "Signed plan payload must not reveal a storage key.");
    }

    public static void TamperedTokenIsRejected()
    {
        var protector = CreateProtector(2);
        var token = protector.Protect(CreatePayload());
        var replacement = token[^1] == 'A' ? 'B' : 'A';
        AssertThrows<UnauthorizedAccessException>(() => protector.Unprotect(token[..^1] + replacement));
    }

    public static void TokenSignedByAnotherKeyIsRejected()
    {
        var token = CreateProtector(3).Protect(CreatePayload());
        AssertThrows<UnauthorizedAccessException>(() => CreateProtector(4).Unprotect(token));
    }

    public static void ShortSigningKeyIsRejected()
    {
        AssertThrows<ArgumentException>(() => new HmacRevisionReadPlanProtector(new byte[31]));
    }

    private static HmacRevisionReadPlanProtector CreateProtector(byte value)
    {
        return new HmacRevisionReadPlanProtector(Enumerable.Repeat(value, 32).ToArray());
    }

    private static RevisionReadPlanPayload CreatePayload()
    {
        var issuedAt = new DateTimeOffset(2026, 8, 6, 0, 0, 0, TimeSpan.Zero);
        return new RevisionReadPlanPayload(
            1,
            Guid.Parse("11111111-1111-1111-1111-111111111111"),
            Guid.Parse("22222222-2222-2222-2222-222222222222"),
            Guid.Parse("33333333-3333-3333-3333-333333333333"),
            Guid.Parse("44444444-4444-4444-4444-444444444444"),
            Guid.Parse("55555555-5555-5555-5555-555555555555"),
            7,
            new string('a', 64),
            42,
            "application/pdf",
            issuedAt,
            issuedAt.AddMinutes(5)
        );
    }

    private static byte[] Decode(string value)
    {
        var normalized = value.Replace('-', '+').Replace('_', '/');
        normalized += new string('=', (4 - normalized.Length % 4) % 4);
        return Convert.FromBase64String(normalized);
    }

    private static void AssertThrows<T>(Action action) where T : Exception
    {
        try
        {
            action();
            throw new InvalidOperationException($"Expected {typeof(T).Name}.");
        }
        catch (T)
        {
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
