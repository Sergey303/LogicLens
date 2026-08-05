using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security.ContractTests;

internal static class InMemoryQuotaContractTests
{
    public static async Task HourlyRequestQuotaResetsAtNextUtcHourAsync()
    {
        var time = new MutableTimeProvider(new DateTimeOffset(
            2026,
            8,
            5,
            7,
            59,
            0,
            TimeSpan.Zero
        ));
        var gate = new InMemoryUploadQuotaGate(
            new UploadQuotaOptions(MaxRequestsPerHour: 2, MaxBytesPerDay: 100),
            time
        );
        var actor = Guid.NewGuid();
        var workspace = Guid.NewGuid();

        await gate.DemandRequestAsync(actor, workspace, CancellationToken.None);
        await gate.DemandRequestAsync(actor, workspace, CancellationToken.None);
        var error = await TestAssert.ThrowsAsync<UploadQuotaExceededException>(
            () => gate.DemandRequestAsync(actor, workspace, CancellationToken.None).AsTask(),
            "Third request in one UTC hour must be rejected."
        );
        TestAssert.Equal(
            "hourly-request-limit",
            error.QuotaCode,
            "Hourly quota code is wrong."
        );

        time.SetUtcNow(time.GetUtcNow().AddMinutes(2));
        await gate.DemandRequestAsync(actor, workspace, CancellationToken.None);
    }

    public static async Task DailyByteQuotaIsIndependentFromRequestQuotaAsync()
    {
        var gate = new InMemoryUploadQuotaGate(
            new UploadQuotaOptions(MaxRequestsPerHour: 50, MaxBytesPerDay: 10),
            new MutableTimeProvider(new DateTimeOffset(
                2026,
                8,
                5,
                7,
                0,
                0,
                TimeSpan.Zero
            ))
        );
        var workspace = Guid.NewGuid();

        await gate.DemandBytesAsync(workspace, 6, CancellationToken.None);
        await gate.DemandBytesAsync(workspace, 4, CancellationToken.None);
        var error = await TestAssert.ThrowsAsync<UploadQuotaExceededException>(
            () => gate.DemandBytesAsync(workspace, 1, CancellationToken.None).AsTask(),
            "Daily byte quota must reject bytes beyond its independent limit."
        );
        TestAssert.Equal("daily-byte-limit", error.QuotaCode, "Daily quota code is wrong.");
    }

    private sealed class MutableTimeProvider : TimeProvider
    {
        private DateTimeOffset _utcNow;

        public MutableTimeProvider(DateTimeOffset utcNow)
        {
            _utcNow = utcNow;
        }

        public override DateTimeOffset GetUtcNow() => _utcNow;

        public void SetUtcNow(DateTimeOffset utcNow)
        {
            _utcNow = utcNow;
        }
    }
}
