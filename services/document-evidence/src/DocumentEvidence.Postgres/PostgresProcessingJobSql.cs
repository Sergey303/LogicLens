namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresProcessingJobSql
{
    public const string FindNextAvailable = """
        SELECT "Id", "State", "Attempt", "MaxAttempts", "AvailableAt",
               "LeaseToken", "LeaseUntil", "LastError"
        FROM "ProcessingJobs"
        WHERE (
            "State" IN ('Pending', 'RetryScheduled')
            AND "AvailableAt" <= @now
        ) OR (
            "State" = 'Leased'
            AND "LeaseUntil" <= @now
        )
        ORDER BY
            CASE WHEN "State" = 'Leased' THEN "LeaseUntil" ELSE "AvailableAt" END,
            "Id"
        LIMIT 1;
        """;

    public const string CompareExchange = """
        UPDATE "ProcessingJobs"
        SET "State" = @replacementState,
            "Attempt" = @replacementAttempt,
            "AvailableAt" = @replacementAvailableAt,
            "LeaseToken" = @replacementLeaseToken,
            "LeaseUntil" = @replacementLeaseUntil,
            "LastError" = @replacementLastError,
            "LastErrorCode" = NULL
        WHERE "Id" = @id
          AND "State" = @expectedState
          AND "Attempt" = @expectedAttempt
          AND "AvailableAt" = @expectedAvailableAt
          AND "LeaseToken" IS NOT DISTINCT FROM @expectedLeaseToken
          AND "LeaseUntil" IS NOT DISTINCT FROM @expectedLeaseUntil
          AND "LastError" IS NOT DISTINCT FROM @expectedLastError;
        """;
}
