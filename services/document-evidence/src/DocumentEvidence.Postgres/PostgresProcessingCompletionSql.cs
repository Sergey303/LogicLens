namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresProcessingCompletionSql
{
    public const string ClaimCompletion = """
        UPDATE "ProcessingJobs"
        SET "State" = 'Succeeded',
            "LeaseToken" = NULL,
            "LeaseUntil" = NULL,
            "LastErrorCode" = NULL,
            "LastError" = NULL
        WHERE "Id" = @jobId
          AND "DocumentRevisionId" = @revisionId
          AND "State" = @expectedState
          AND "Attempt" = @expectedAttempt
          AND "AvailableAt" = @expectedAvailableAt
          AND "LeaseToken" IS NOT DISTINCT FROM @expectedLeaseToken
          AND "LeaseUntil" IS NOT DISTINCT FROM @expectedLeaseUntil
          AND "LastError" IS NOT DISTINCT FROM @expectedLastError;
        """;

    public const string UpdateRevision = """
        UPDATE "DocumentRevisions"
        SET "State" = 'Processed',
            "Adapter" = @adapter,
            "AdapterVersion" = @adapterVersion,
            "ManifestHash" = @manifestHash,
            "ManifestJson" = @manifestJson
        WHERE "Id" = @revisionId;
        """;

    public const string InsertFragment = """
        INSERT INTO "DocumentFragments" (
            "Id", "DocumentRevisionId", "Sequence", "Kind",
            "AnchorJson", "Text", "ContentHash"
        ) VALUES (
            @id, @revisionId, @sequence, @kind,
            @anchorJson, @text, @contentHash
        );
        """;

    public const string InsertOutbox = """
        INSERT INTO "DocumentEvidenceOutbox" (
            "Id", "EventKey", "EventType", "AggregateId", "PayloadJson",
            "CreatedAt", "AvailableAt", "Attempt"
        ) VALUES (
            @id, @eventKey, 'document.revision.processed', @revisionId,
            @payloadJson::jsonb, @completedAt, @completedAt, 0
        );
        """;
}
