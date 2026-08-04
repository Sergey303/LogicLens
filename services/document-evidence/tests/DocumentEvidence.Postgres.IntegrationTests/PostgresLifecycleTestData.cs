using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal static class PostgresLifecycleTestData
{
    public static UploadCompletionCommit CreateCommit(
        Guid workspaceId,
        Guid documentId,
        string idempotencyKey,
        char hashCharacter = 'a'
    )
    {
        var hash = new string(hashCharacter, 64);
        var storedObject = new StoredObjectReference(
            hash,
            12,
            $"sha256/{hash[..2]}/{hash[2..4]}/{hash}",
            true
        );
        var manifest = RevisionManifestFactory.Create(
            storedObject,
            "application/pdf",
            "Upload",
            "pypdf",
            "1.0.0"
        );
        return new UploadCompletionCommit(
            workspaceId,
            documentId,
            idempotencyKey,
            storedObject,
            manifest
        );
    }
}
