namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal static class SecureUploadOrderingContractTests
{
    public static async Task AccessDenialStopsBeforeBodyReadAsync()
    {
        var fixture = new SecureUploadTestFixture();
        using var stream = new ReadTrackingStream(SecureUploadTestFixture.PdfBytes());
        var service = fixture.CreateService(denyAuthorization: true);

        await TestAssert.ThrowsAsync<UnauthorizedAccessException>(
            () => service.CompleteAsync(SecureUploadTestFixture.Command(stream)),
            "Unauthorized upload must fail."
        );

        TestAssert.Equal(0, stream.ReadCalls, "Authorization denial must precede body reads.");
        TestAssert.Equal(0, fixture.Store.Writes, "Authorization denial must precede storage.");
        TestAssert.True(
            fixture.Events.SequenceEqual(["authorization"]),
            "Authorization must be the only admission operation after denial."
        );
        TestAssert.Equal(
            "rejected:access-denied",
            fixture.Audit.Records.Single().Outcome,
            "Access denial audit outcome is wrong."
        );
    }

    public static async Task HourlyQuotaStopsBeforeBodyReadAsync()
    {
        var fixture = new SecureUploadTestFixture();
        using var stream = new ReadTrackingStream(SecureUploadTestFixture.PdfBytes());
        var service = fixture.CreateService(denyRequestQuota: true);

        await TestAssert.ThrowsAsync<UploadQuotaExceededException>(
            () => service.CompleteAsync(SecureUploadTestFixture.Command(stream)),
            "Hourly request quota must fail closed."
        );

        TestAssert.Equal(0, stream.ReadCalls, "Request quota must precede body reads.");
        TestAssert.Equal(0, fixture.Store.Writes, "Request quota must precede storage.");
        TestAssert.True(
            fixture.Events.SequenceEqual(["authorization", "quota:request"]),
            "Request quota ordering is wrong."
        );
    }

    public static async Task DeclaredSizeLimitStopsBeforeBodyReadAsync()
    {
        var fixture = new SecureUploadTestFixture();
        using var stream = new ReadTrackingStream(SecureUploadTestFixture.PdfBytes());
        var service = fixture.CreateService(new SecureUploadOptions(MaxUploadBytes: 8));

        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => service.CompleteAsync(
                SecureUploadTestFixture.Command(stream, declaredLength: 100)
            ),
            "Oversized declared upload must fail."
        );

        TestAssert.Equal(0, stream.ReadCalls, "Declared length must be checked before body reads.");
        TestAssert.Equal(0, fixture.Store.Writes, "Oversized upload must not reach storage.");
    }

    public static async Task InvalidSignatureStopsBeforeByteQuotaAsync()
    {
        var fixture = new SecureUploadTestFixture();
        using var stream = new ReadTrackingStream("not a pdf"u8.ToArray());
        var service = fixture.CreateService();

        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => service.CompleteAsync(SecureUploadTestFixture.Command(stream)),
            "Mismatched upload signature must fail."
        );

        TestAssert.True(stream.ReadCalls > 0, "Signature validation requires quarantine bytes.");
        TestAssert.True(
            fixture.Events.SequenceEqual(["authorization", "quota:request"]),
            "Invalid signature must not consume the daily byte quota."
        );
        TestAssert.Equal(0, fixture.Store.Writes, "Invalid signature must not reach storage.");
    }

    public static async Task DailyByteQuotaStopsBeforeStorageAsync()
    {
        var fixture = new SecureUploadTestFixture();
        var bytes = SecureUploadTestFixture.PdfBytes();
        using var stream = new ReadTrackingStream(bytes);
        var service = fixture.CreateService(denyByteQuota: true);

        await TestAssert.ThrowsAsync<UploadQuotaExceededException>(
            () => service.CompleteAsync(
                SecureUploadTestFixture.Command(stream, declaredLength: bytes.LongLength)
            ),
            "Daily byte quota must fail closed."
        );

        TestAssert.True(
            fixture.Events.SequenceEqual([
                "authorization",
                "quota:request",
                $"quota:bytes:{bytes.LongLength}",
            ]),
            "Daily byte quota must run after quarantine and before storage."
        );
        TestAssert.Equal(0, fixture.Store.Writes, "Daily quota denial must prevent storage.");
    }
}
