namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await using var database = await PostgresTestDatabase.CreateAsync();
        await PostgresCommitIntegrationTests.CommitAndReplayAreAtomicAsync(database);
        await PostgresCommitIntegrationTests.ConcurrentCommitsSerializeRevisionNumbersAsync(database);
        await PostgresRollbackIntegrationTests.OutboxFailureRollsBackLifecycleAsync(database);
        await PostgresProcessingIntegrationTests.ConcurrentWorkersAcquireOneLeaseAsync(database);
        await PostgresProcessingIntegrationTests.ExpiredLeaseIsReclaimedAsync(database);
        await PostgresRetryIntegrationTests.RetryThenTerminalIsDurableAsync(database);
        await PostgresCompletionIntegrationTests.CompletionPersistsManifestFragmentsAndOutboxAsync(database);
        await PostgresCompletionIntegrationTests.StaleLeaseRollsBackAllOutputAsync(database);
        await PostgresProtectedRevisionIntegrationTests.LocatorReturnsRevocationAndObjectIdentityAsync(database);
        await PostgresProtectedRevisionIntegrationTests.LocatorMarksOlderRevisionSupersededAsync(database);
        Console.WriteLine("Document Evidence PostgreSQL integration tests passed.");
        return 0;
    }
}
