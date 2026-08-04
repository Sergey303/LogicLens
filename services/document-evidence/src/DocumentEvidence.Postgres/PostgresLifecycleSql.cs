namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresLifecycleSql
{
    public const string FindCompletion = """
        SELECT d."WorkspaceId", d."Id", r."Id", r."RevisionNumber",
               o."Id", j."Id", r."ManifestHash"
        FROM "ProcessingJobs" AS j
        JOIN "DocumentRevisions" AS r ON r."Id" = j."DocumentRevisionId"
        JOIN "Documents" AS d ON d."Id" = r."DocumentId"
        JOIN "StoredObjects" AS o ON o."Id" = r."StoredObjectId"
        WHERE j."IdempotencyKey" = @idempotencyKey
          AND d."WorkspaceId" = @workspaceId
        LIMIT 1;
        """;

    public const string LockDocument = """
        SELECT "CurrentRevisionNumber"
        FROM "Documents"
        WHERE "Id" = @documentId
          AND "WorkspaceId" = @workspaceId
          AND "IsRevoked" = FALSE
        FOR UPDATE;
        """;

    public const string InsertStoredObject = """
        INSERT INTO "StoredObjects"
            ("Id", "Sha256", "StorageKey", "SizeBytes", "MediaType")
        VALUES
            (@id, @sha256, @storageKey, @sizeBytes, @mediaType)
        ON CONFLICT ("Sha256") DO NOTHING
        RETURNING "Id";
        """;

    public const string FindStoredObject = """
        SELECT "Id", "StorageKey", "SizeBytes", "MediaType"
        FROM "StoredObjects"
        WHERE "Sha256" = @sha256;
        """;

    public const string InsertRevision = """
        INSERT INTO "DocumentRevisions"
            ("Id", "DocumentId", "StoredObjectId", "RevisionNumber", "State",
             "Adapter", "AdapterVersion", "ManifestHash", "ManifestJson")
        VALUES
            (@id, @documentId, @storedObjectId, @revisionNumber, 'Pending',
             @adapter, @adapterVersion, @manifestHash, @manifestJson);
        """;

    public const string InsertProcessingJob = """
        INSERT INTO "ProcessingJobs"
            ("Id", "DocumentRevisionId", "Kind", "State", "Attempt", "MaxAttempts",
             "IdempotencyKey", "AvailableAt", "LeaseToken", "LeaseUntil",
             "LastErrorCode", "LastError")
        VALUES
            (@id, @revisionId, @kind, 'Pending', 0, @maxAttempts,
             @idempotencyKey, @availableAt, NULL, NULL, NULL, NULL);
        """;

    public const string UpdateDocument = """
        UPDATE "Documents"
        SET "CurrentRevisionNumber" = @revisionNumber,
            "State" = 'Processing'
        WHERE "Id" = @documentId
          AND "WorkspaceId" = @workspaceId;
        """;

    public const string InsertOutbox = """
        INSERT INTO "DocumentEvidenceOutbox"
            ("Id", "EventKey", "EventType", "AggregateId", "PayloadJson",
             "CreatedAt", "AvailableAt", "Attempt")
        VALUES
            (@id, @eventKey, 'document.revision.created', @aggregateId,
             CAST(@payloadJson AS jsonb), @createdAt, @availableAt, 0);
        """;
}
