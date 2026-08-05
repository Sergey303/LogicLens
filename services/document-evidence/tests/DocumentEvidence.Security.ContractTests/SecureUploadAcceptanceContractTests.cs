namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal static class SecureUploadAcceptanceContractTests
{
    public static async Task AcceptedUploadNormalizesNameAndAuditsWithoutPathAsync()
    {
        var fixture = new SecureUploadTestFixture();
        var bytes = SecureUploadTestFixture.PdfBytes();
        using var stream = new ReadTrackingStream(bytes);
        var service = fixture.CreateService();

        var result = await service.CompleteAsync(
            SecureUploadTestFixture.Command(stream, declaredLength: bytes.LongLength)
        );

        TestAssert.Equal(
            "demo evidence.pdf",
            result.DisplayName,
            "Display name must be reduced to a normalized safe base name."
        );
        TestAssert.Equal(1, fixture.Store.Writes, "Accepted upload must write one immutable object.");
        TestAssert.True(
            fixture.Events.SequenceEqual([
                "authorization",
                "quota:request",
                $"quota:bytes:{bytes.LongLength}",
                "repository:find",
                "storage",
                "repository:commit",
            ]),
            "Accepted upload boundary ordering is wrong."
        );
        var audit = fixture.Audit.Records.Single();
        TestAssert.Equal("accepted", audit.Outcome, "Accepted audit outcome is wrong.");
        TestAssert.Equal(bytes.LongLength, audit.SizeBytes, "Accepted audit size is wrong.");
        TestAssert.True(
            audit.GetType().GetProperty("ObjectKey") is null
                && audit.GetType().GetProperty("DisplayName") is null
                && audit.GetType().GetProperty("IdempotencyKey") is null,
            "Audit contract must not expose paths, display names, or idempotency keys."
        );
    }

    public static void DisplayNameRejectsEmptyTraversalAndControlNames()
    {
        foreach (var value in new[] { "..", "/", "bad\u0001name.pdf" })
        {
            _ = TestAssert.ThrowsAsync<ArgumentException>(
                () => Task.Run(() => UploadDisplayName.Normalize(value, 180)),
                $"Unsafe display name must fail: {value}"
            ).GetAwaiter().GetResult();
        }
    }
}
