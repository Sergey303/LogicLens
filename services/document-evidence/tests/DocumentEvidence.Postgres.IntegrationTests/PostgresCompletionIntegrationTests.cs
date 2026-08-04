using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresCompletionIntegrationTests
{
    public static async Task CompletionPersistsManifestFragmentsAndOutboxAsync(
        PostgresTestDatabase database
    )
    {
        await database.ResetAsync();
        var fixture = await SeedLeasedJobAsync(database.DataSource);
        var service = new ProcessingCompletionService(
            new PostgresProcessingCompletionRepository(database.DataSource)
        );

        await service.CompleteAsync(fixture.Job, Completion(fixture.RevisionId));

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
        var fixture = await SeedLeasedJobAsync(database.DataSource);
        var stale = fixture.Job with { LeaseToken = Guid.NewGuid() };
        var service = new ProcessingCompletionService(
            new PostgresProcessingCompletionRepository(database.DataSource)
        );

        await AssertThrowsAsync<InvalidOperationException>(() =>
            service.CompleteAsync(stale, Completion(fixture.RevisionId))
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

    private static async Task<CompletionFixture> SeedLeasedJobAsync(NpgsqlDataSource dataSource)
    {
        var documentId = Guid.NewGuid();
        var objectId = Guid.NewGuid();
        var revisionId = Guid.NewGuid();
        var jobId = Guid.NewGuid();
        var leaseToken = Guid.NewGuid();
        var availableAt = DateTimeOffset.Parse("2026-08-04T15:00:00Z");
        var leaseUntil = availableAt.AddMinutes(5);
        const string sql = """
            INSERT INTO "Documents" VALUES
                (@documentId, @workspaceId, 'Evidence.pdf', 'application/pdf', 'Upload', 'Processing', 1, FALSE);
            INSERT INTO "StoredObjects" VALUES
                (@objectId, @hash, 'sha256/aa/object', 100, 'application/pdf');
            INSERT INTO "DocumentRevisions" VALUES
                (@revisionId, @documentId, @objectId, 1, 'Processing', NULL, NULL, NULL, NULL);
            INSERT INTO "ProcessingJobs" VALUES
                (@jobId, @revisionId, 'ExtractPdf', 'Leased', 1, 3, @idempotencyKey,
                 @availableAt, @leaseToken, @leaseUntil, NULL, NULL);
            """;
        await using var command = dataSource.CreateCommand(sql);
        command.Parameters.AddWithValue("documentId", documentId);
        command.Parameters.AddWithValue("workspaceId", Guid.NewGuid());
        command.Parameters.AddWithValue("objectId", objectId);
        command.Parameters.AddWithValue("revisionId", revisionId);
        command.Parameters.AddWithValue("jobId", jobId);
        command.Parameters.AddWithValue("hash", new string('a', 64));
        command.Parameters.AddWithValue("idempotencyKey", $"job:{jobId}");
        command.Parameters.AddWithValue("availableAt", availableAt.UtcDateTime);
        command.Parameters.AddWithValue("leaseToken", leaseToken);
        command.Parameters.AddWithValue("leaseUntil", leaseUntil.UtcDateTime);
        _ = await command.ExecuteNonQueryAsync();
        return new CompletionFixture(
            revisionId,
            new ProcessingJobSnapshot(
                jobId,
                ProcessingJobState.Leased,
                1,
                3,
                availableAt,
                leaseToken,
                leaseUntil,
                null
            )
        );
    }

    private static ProcessingCompletionPayload Completion(Guid revisionId)
    {
        var hash = new string('d', 64);
        return new ProcessingCompletionPayload(
            revisionId,
            DateTimeOffset.Parse("2026-08-04T15:04:00Z"),
            new ProcessingArtifactManifest("poppler-bbox-layout", "24.02.0", hash, hash, hash, "{}", hash),
            [new ProcessingFragmentWrite(Guid.NewGuid(), revisionId, 1, "paragraph", "{}", "Evidence", hash)]
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

    private sealed record CompletionFixture(Guid RevisionId, ProcessingJobSnapshot Job);
}
