using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresRetryIntegrationTests
{
    public static async Task RetryThenTerminalIsDurableAsync(PostgresTestDatabase database)
    {
        var now = DateTimeOffset.UtcNow.AddMinutes(1);
        await PostgresProcessingTestData.SeedJobAsync(database, maxAttempts: 2);
        var coordinator = new ProcessingJobCoordinator(
            new PostgresProcessingJobRepository(database.DataSource)
        );
        var first = await coordinator.TryLeaseNextAsync(
            now,
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        ) ?? throw new InvalidOperationException("First retry lease was not acquired.");
        var retry = await coordinator.FailAsync(
            first,
            first.LeaseToken!.Value,
            now.AddSeconds(1),
            "transient",
            TimeSpan.FromSeconds(30),
            TimeSpan.FromMinutes(5)
        );
        var early = await coordinator.TryLeaseNextAsync(
            retry.AvailableAt.AddMilliseconds(-1),
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        );
        var second = await coordinator.TryLeaseNextAsync(
            retry.AvailableAt,
            TimeSpan.FromMinutes(5),
            Guid.NewGuid()
        ) ?? throw new InvalidOperationException("Scheduled retry was not leased.");
        var terminal = await coordinator.FailAsync(
            second,
            second.LeaseToken!.Value,
            retry.AvailableAt.AddSeconds(1),
            "permanent",
            TimeSpan.FromSeconds(30),
            TimeSpan.FromMinutes(5)
        );

        TestAssert.True(early is null, "Durable retry leased before AvailableAt.");
        TestAssert.Equal(ProcessingJobState.FailedTerminal, terminal.State, "Final failure not terminal.");
        TestAssert.Equal(
            "FailedTerminal",
            await PostgresProcessingTestData.CurrentStateAsync(database),
            "Terminal state not persisted."
        );
    }
}
