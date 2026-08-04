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
        await SeedAsync(database, workspaceId, documentId, objectId, revisionId, hash);
        var locator = new PostgresProtectedRevisionObjectLocator(database.DataSource);

        var result = await locator.FindAsync(workspaceId, revisionId, CancellationToken.None);

        TestAssert.True(result is not null, "Protected revision metadata must be found.");
        TestAssert.Equal(workspaceId, result!.WorkspaceId);
        TestAssert.Equal(revisionId, result.RevisionId);
        TestAssert.Equal(hash, result.Sha256);
        TestAssert.True(result.IsRevoked, "Revocation state must come from the document row.");
        TestAssert.True(
            await locator.FindAsync(Guid.NewGuid(), revisionId, CancellationToken.None) is null,
            "A revision must not be resolved through another workspace."
        );
    }

    private static Task SeedAsync(
        PostgresTestDatabase database,
        Guid workspaceId,
        Guid documentId,
        Guid objectId,
        Guid revisionId,
        string hash
    )
    {
        var sql = $"""
            INSERT INTO "Documents" VALUES
                ('{documentId}', '{workspaceId}', 'Revoked.pdf', 'application/pdf',
                 'Upload', 'Processed', 1, TRUE);
            INSERT INTO "StoredObjects" VALUES
                ('{objectId}', '{hash}', 'sha256/bb/object', 42, 'application/pdf');
            INSERT INTO "DocumentRevisions" VALUES
                ('{revisionId}', '{documentId}', '{objectId}', 1, 'Processed',
                 'poppler-bbox-layout', '24.02.0', '{hash}', '{{}}');
            """;
        return database.ExecuteAsync(sql);
    }
}
