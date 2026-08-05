namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresProcessingTestData
{
    public static async Task SeedJobAsync(PostgresTestDatabase database, int maxAttempts)
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

    public static Task<string> CurrentStateAsync(PostgresTestDatabase database)
    {
        return database.ScalarAsync<string>("SELECT \"State\" FROM \"ProcessingJobs\" LIMIT 1;");
    }
}
