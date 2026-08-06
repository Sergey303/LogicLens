namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresProtectedRevisionIntegrationTests
{
    public static async Task LocatorReturnsRevocationAndObjectIdentityAsync(
        PostgresTestDatabase database
    )
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var documentId = Guid.NewGuid();
        var objectId = Guid.NewGuid();
        var revisionId = Guid.NewGuid();
        var hash = new string('b', 64);
        await SeedAsync(
            database,
            workspaceId,
            documentId,
            objectId,
            revisionId,
            hash,
            currentRevisionNumber: 1,
            revisionNumber: 1,
            isRevoked: true
        );
        var locator = new PostgresProtectedRevisionObjectLocator(database.DataSource);

        var result = await locator.FindAsync(workspaceId, revisionId, CancellationToken.None);

        TestAssert.True(result is not null, "Protected revision metadata must be found.");
        TestAssert.Equal(workspaceId, result!.WorkspaceId, "Workspace identity must be preserved.");
        TestAssert.Equal(revisionId, result.RevisionId, "Revision identity must be preserved.");
        TestAssert.Equal(1, result.RevisionNumber, "Revision number must come from the revision row.");
        TestAssert.Equal(hash, result.Sha256, "Locator must return immutable object identity.");
        TestAssert.True(result.IsRevoked, "Revocation state must come from the document row.");
        TestAssert.True(!result.IsSuperseded, "The current revision must not be superseded.");
        TestAssert.True(
            await locator.FindAsync(Guid.NewGuid(), revisionId, CancellationToken.None) is null,
            "A revision must not be resolved through another workspace."
        );
    }

    public static async Task LocatorMarksOlderRevisionSupersededAsync(PostgresTestDatabase database)
    {
        await database.ResetAsync();
        var workspaceId = Guid.NewGuid();
        var revisionId = Guid.NewGuid();
        await SeedAsync(
            database,
            workspaceId,
            Guid.NewGuid(),
            Guid.NewGuid(),
            revisionId,
            new string('c', 64),
            currentRevisionNumber: 2,
            revisionNumber: 1,
            isRevoked: false
        );
        var locator = new PostgresProtectedRevisionObjectLocator(database.DataSource);

        var result = await locator.FindAsync(workspaceId, revisionId, CancellationToken.None);

        TestAssert.True(result is not null, "Older revision metadata must be found.");
        TestAssert.True(result!.IsSuperseded, "Older revision must be marked superseded.");
        TestAssert.True(!result.IsRevoked, "Supersede and revocation must remain independent.");
    }

    private static async Task SeedAsync(
        PostgresTestDatabase database,
        Guid workspaceId,
        Guid documentId,
        Guid objectId,
        Guid revisionId,
        string hash,
        int currentRevisionNumber,
        int revisionNumber,
        bool isRevoked
    )
    {
        const string sql = """
            INSERT INTO "Documents" VALUES
                (@documentId, @workspaceId, 'Protected.pdf', 'application/pdf',
                 'Upload', 'Processed', @currentRevisionNumber, @isRevoked);
            INSERT INTO "StoredObjects" VALUES
                (@objectId, @hash, 'sha256/protected/object', 42, 'application/pdf');
            INSERT INTO "DocumentRevisions" VALUES
                (@revisionId, @documentId, @objectId, @revisionNumber, 'Processed',
                 'poppler-bbox-layout', '24.02.0', @hash, @manifestJson);
            """;
        await using var command = database.DataSource.CreateCommand(sql);
        command.Parameters.AddWithValue("documentId", documentId);
        command.Parameters.AddWithValue("workspaceId", workspaceId);
        command.Parameters.AddWithValue("objectId", objectId);
        command.Parameters.AddWithValue("revisionId", revisionId);
        command.Parameters.AddWithValue("hash", hash);
        command.Parameters.AddWithValue("currentRevisionNumber", currentRevisionNumber);
        command.Parameters.AddWithValue("revisionNumber", revisionNumber);
        command.Parameters.AddWithValue("isRevoked", isRevoked);
        command.Parameters.AddWithValue("manifestJson", "{}");
        _ = await command.ExecuteNonQueryAsync();
    }
}
