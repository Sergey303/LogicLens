using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresProcessingIntegrationTests
{
    public static async Task ConcurrentWorkersAcquireOneLeaseAsync(
        PostgresTestDatabase database
    )
    {
        var now = DateTimeOffset.UtcNow.AddMinutes(1);
        await SeedJobAsync(database, maxAttempts: 3);
        var repository = new PostgresProcessingJobRepository(database.DataSource);
        var first = new ProcessingJobCoordinator(repository);
        var second = new ProcessingJobCoordinator(repository);

        var leases = await Task.WhenAll(
            first.TryLeaseNextAsync(now, TimeSpan.FromMinutes(5), Guid.NewGuid()),
            second.TryLeaseNextAsync(now, TimeSpan.FromMinutes(5), Guid.NewGuid())
        );
        var leased = leases.Single(result => result is not null)!;

        TestAssert.Equal(1, leases.Count(result => result is not null), "Two workers acquired one job.");
        TestAssert.Equal(1, leased.Attempt, "First durable lease has wrong attempt.");
        var completed = await first.CompleteAsync(
            leased,
            leased.LeaseToken!.Value,
            now.AddMinutes(1)
        );
        TestAssert.Equal(ProcessingJobState.Succeeded, completed.State, "Completion was not persisted.");
        TestAssert.Equal("Succeeded", await CurrentStateAsync(database), "Database state is not succeeded.");
    }

    public static async Task ExpiredLeaseIsReclaimedAsync(PostgresTestDatabase database)
    {
        var now = DateTimeOffset.UtcNow.AddMinutes(1);
        await SeedJobAsync(database, maxAttempts: 3);
        var coordinator = new ProcessingJobCoordinator(
            new PostgresProcessingJobRepository(database.DataSource)
        );
        var first = await coordinator.TryLeaseNextAsync(
            now,
            TimeSpan.FromMinutes(1),
            Guid.NewGuid()
        ) ?? throw new InvalidOperationException("First durable lease was not acquired.");
        var secondToken = Guid.NewGuid();
        var reclaimed = await coordinator.TryLeaseNextAsync(
            now.AddMinutes(2),
            TimeSpan.FromMinutes(5),
            secondToken
        );

        TestAssert.True(reclaimed is not null, "Expired durable lease was not reclaimed.");
        TestAssert.Equal(2, reclaimed!.Attempt, "Reclaimed durable lease has wrong attempt.");
        TestAssert.Equal(secondToken, reclaimed.LeaseToken!.Value, "Reclaim retained stale token.");
        TestAssert.True(first.LeaseToken != reclaimed.LeaseToken, "Lease token was not replaced.");
    }

    public static async Task RetryThenTerminalIsDurableAsync(PostgresTestDatabase database)
    {
        var now = DateTimeOffset.UtcNow.AddMinutes(1);
        await SeedJobAsync(database, maxAttempts: 2);
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
        TestAssert.Equal("FailedTerminal", await CurrentStateAsync(database), "Terminal state not persisted.");
    }

    private static async Task SeedJobAsync(PostgresTestDatabase database, int maxAttempts)
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        await database.SeedDocumentAsync(workspaceId, documentId);
        var upload = new PostgresDocumentLifecycleRepository(
            database.DataSource,
            new PostgresLifecycleOptions(MaxAttempts: maxAttempts)
        );
        var commit = PostgresLifecycleTestData.CreateCommit(
            workspaceId,
            documentId,
            $"upload:{Guid.NewGuid():N}"
        );
        _ = await upload.CommitUploadAndEnqueueProcessingAsync(commit, CancellationToken.None);
    }

    private static Task<string> CurrentStateAsync(PostgresTestDatabase database)
    {
        return database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;");
    }
}
