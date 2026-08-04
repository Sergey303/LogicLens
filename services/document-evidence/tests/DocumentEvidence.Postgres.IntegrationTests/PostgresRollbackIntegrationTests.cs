using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresRollbackIntegrationTests
{
    public static async Task OutboxFailureRollsBackLifecycleAsync(
        PostgresTestDatabase database
    )
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        await database.SeedDocumentAsync(workspaceId, documentId);
        await database.ExecuteAsync("DROP TABLE \"DocumentEvidenceOutbox\";");
        var repository = new PostgresDocumentLifecycleRepository(database.DataSource);
        var commit = PostgresLifecycleTestData.CreateCommit(
            workspaceId,
            documentId,
            $"upload:{Guid.NewGuid():N}"
        );

        await TestAssert.ThrowsAsync<PostgresException>(
            () => repository.CommitUploadAndEnqueueProcessingAsync(
                commit,
                CancellationToken.None
            ),
            "Missing outbox table did not fail the lifecycle transaction."
        );

        TestAssert.Equal(0L, await CountAsync(database, "StoredObjects"), "Stored object was not rolled back.");
        TestAssert.Equal(0L, await CountAsync(database, "DocumentRevisions"), "Revision was not rolled back.");
        TestAssert.Equal(0L, await CountAsync(database, "ProcessingJobs"), "Job was not rolled back.");
        TestAssert.Equal(0, await database.ScalarAsync<int>(
            "SELECT \"CurrentRevisionNumber\" FROM \"Documents\" LIMIT 1;"
        ), "Document pointer advanced despite rollback.");
    }

    private static Task<long> CountAsync(PostgresTestDatabase database, string table)
    {
        return database.ScalarAsync<long>($"SELECT COUNT(*) FROM \"{table}\";");
    }
}
