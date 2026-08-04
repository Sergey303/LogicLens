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
            await database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;")
        );
        TestAssert.Equal(
            1L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentFragments\";")
        );
        TestAssert.Equal(
            new string('d', 64),
            await database.ScalarAsync<string>(
                "SELECT \"ManifestHash\" FROM \"DocumentRevisions\" LIMIT 1;"
            )
        );
        TestAssert.Equal(
            1L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentEvidenceOutbox\";")
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
            await database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;")
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentFragments\";")
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>(
                "SELECT COUNT(\"ManifestHash\") FROM \"DocumentRevisions\";"
            )
        );
        TestAssert.Equal(
            0L,
            await database.ScalarAsync<long>("SELECT COUNT(*) FROM \"DocumentEvidenceOutbox\";")
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
