namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresCommitIntegrationTests
{
    public static async Task CommitAndReplayAreAtomicAsync(PostgresTestDatabase database)
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        await database.SeedDocumentAsync(workspaceId, documentId);
        var repository = new PostgresDocumentLifecycleRepository(
            database.DataSource,
            new PostgresLifecycleOptions(MaxAttempts: 4)
        );
        var commit = PostgresLifecycleTestData.CreateCommit(
            workspaceId,
            documentId,
            $"upload:{Guid.NewGuid():N}"
        );

        var first = await repository.CommitUploadAndEnqueueProcessingAsync(
            commit,
            CancellationToken.None
        );
        var replay = await repository.CommitUploadAndEnqueueProcessingAsync(
            commit,
            CancellationToken.None
        );

        TestAssert.True(!first.Replayed, "First PostgreSQL commit was marked as replayed.");
        TestAssert.True(replay.Replayed, "Repeated PostgreSQL commit was not replayed.");
        TestAssert.Equal(first.RevisionId, replay.RevisionId, "Replay changed revision identity.");
        TestAssert.Equal(first.ProcessingJobId, replay.ProcessingJobId, "Replay changed job identity.");
        TestAssert.Equal(1L, await CountAsync(database, "DocumentRevisions"), "Revision duplicated.");
        TestAssert.Equal(1L, await CountAsync(database, "ProcessingJobs"), "Job duplicated.");
        TestAssert.Equal(1L, await CountAsync(database, "DocumentEvidenceOutbox"), "Outbox duplicated.");
        TestAssert.Equal(1, await database.ScalarAsync<int>(
            "SELECT \"CurrentRevisionNumber\" FROM \"Documents\" LIMIT 1;"
        ), "Document revision pointer was not advanced.");
        TestAssert.Equal(4, await database.ScalarAsync<int>(
            "SELECT \"MaxAttempts\" FROM \"ProcessingJobs\" LIMIT 1;"
        ), "Job policy was not persisted.");
    }

    public static async Task ConcurrentCommitsSerializeRevisionNumbersAsync(
        PostgresTestDatabase database
    )
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        await database.SeedDocumentAsync(workspaceId, documentId);
        var repository = new PostgresDocumentLifecycleRepository(database.DataSource);
        var firstCommit = PostgresLifecycleTestData.CreateCommit(
            workspaceId,
            documentId,
            $"upload:{Guid.NewGuid():N}",
            'a'
        );
        var secondCommit = PostgresLifecycleTestData.CreateCommit(
            workspaceId,
            documentId,
            $"upload:{Guid.NewGuid():N}",
            'b'
        );

        var results = await Task.WhenAll(
            repository.CommitUploadAndEnqueueProcessingAsync(firstCommit, CancellationToken.None),
            repository.CommitUploadAndEnqueueProcessingAsync(secondCommit, CancellationToken.None)
        );

        TestAssert.True(
            results.Select(result => result.RevisionNumber).Order().SequenceEqual([1, 2]),
            "Concurrent commits did not serialize revision numbering."
        );
        TestAssert.Equal(2L, await CountAsync(database, "DocumentRevisions"), "Revision count wrong.");
        TestAssert.Equal(2L, await CountAsync(database, "ProcessingJobs"), "Job count wrong.");
        TestAssert.Equal(2L, await CountAsync(database, "DocumentEvidenceOutbox"), "Outbox count wrong.");
    }

    private static Task<long> CountAsync(PostgresTestDatabase database, string table)
    {
        return database.ScalarAsync<long>($"SELECT COUNT(*) FROM \"{table}\";");
    }
}
