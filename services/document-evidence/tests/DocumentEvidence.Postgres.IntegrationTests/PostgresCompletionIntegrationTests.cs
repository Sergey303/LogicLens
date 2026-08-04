using KnowledgePilot.LogicLens.DocumentEvidence.Application;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresCompletionIntegrationTests
{
    public static async Task CompletionPersistsManifestFragmentsAndOutboxAsync(
        PostgresTestDatabase database
    )
    {
        await database.ResetAsync();
        var fixture = await PostgresCompletionTestData.SeedLeasedJobAsync(database.DataSource);
        var service = new ProcessingCompletionService(
            new PostgresProcessingCompletionRepository(database.DataSource)
        );

        await service.CompleteAsync(
            fixture.Job,
            PostgresCompletionTestData.Completion(fixture.RevisionId)
        );

        TestAssert.Equal(
            "Succeeded",
            await database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;"),
            "Processing completion must persist terminal success."
        );
        TestAssert.Equal(
            1L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentFragments\";"),
            "Processing completion must persist canonical fragments."
        );
        TestAssert.Equal(
            new string('d', 64),
            await database.ScalarAsync<string>(
                "SELECT \"ManifestHash\" FROM \"DocumentRevisions\" LIMIT 1;"
            ),
            "Processing completion must persist parser manifest identity."
        );
        TestAssert.Equal(
            1L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentEvidenceOutbox\";"),
            "Processing completion must emit one durable event."
        );
    }

    public static async Task StaleLeaseRollsBackAllOutputAsync(PostgresTestDatabase database)
    {
        await database.ResetAsync();
        var fixture = await PostgresCompletionTestData.SeedLeasedJobAsync(database.DataSource);
        var stale = fixture.Job with { LeaseToken = Guid.NewGuid() };
        var service = new ProcessingCompletionService(
            new PostgresProcessingCompletionRepository(database.DataSource)
        );

        await AssertThrowsAsync<InvalidOperationException>(() =>
            service.CompleteAsync(stale, PostgresCompletionTestData.Completion(fixture.RevisionId))
        );

        TestAssert.Equal(
            "Leased",
            await database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;"),
            "A stale worker must not change the persisted job state."
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentFragments\";"),
            "A stale worker must not persist fragments."
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>(
                "SELECT COUNT(\"ManifestHash\") FROM \"DocumentRevisions\";"
            ),
            "A stale worker must not persist parser manifest identity."
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentEvidenceOutbox\";"),
            "A stale worker must not emit an outbox event."
        );
    }

    private static async Task AssertThrowsAsync<T>(Func<Task> action) where T : Exception
    {
        try
        {
            await action();
            throw new InvalidOperationException($"Expected {typeof(T).Name}.");
        }
        catch (T)
        {
        }
    }
}
