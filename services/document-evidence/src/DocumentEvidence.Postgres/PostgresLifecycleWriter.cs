using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresLifecycleWriter
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public static async Task WriteAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        PostgresLifecycleOptions options,
        DateTimeOffset now,
        Guid storedObjectId,
        Guid revisionId,
        int revisionNumber,
        Guid processingJobId,
        CancellationToken cancellationToken
    )
    {
        await InsertRevisionAsync(
            connection,
            transaction,
            commit,
            storedObjectId,
            revisionId,
            revisionNumber,
            cancellationToken
        );
        await InsertProcessingJobAsync(
            connection,
            transaction,
            commit,
            options,
            now,
            revisionId,
            processingJobId,
            cancellationToken
        );
        await UpdateDocumentAsync(
            connection,
            transaction,
            commit,
            revisionNumber,
            cancellationToken
        );
        await InsertOutboxAsync(
            connection,
            transaction,
            commit,
            now,
            revisionId,
            processingJobId,
            cancellationToken
        );
    }

    private static async Task InsertRevisionAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        Guid storedObjectId,
        Guid revisionId,
        int revisionNumber,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.InsertRevision,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", revisionId);
        command.Parameters.AddWithValue("documentId", commit.DocumentId);
        command.Parameters.AddWithValue("storedObjectId", storedObjectId);
        command.Parameters.AddWithValue("revisionNumber", revisionNumber);
        command.Parameters.AddWithValue("adapter", commit.Manifest.Adapter);
        command.Parameters.AddWithValue("adapterVersion", commit.Manifest.AdapterVersion);
        command.Parameters.AddWithValue("manifestHash", commit.Manifest.Sha256);
        command.Parameters.AddWithValue("manifestJson", commit.Manifest.CanonicalJson);
        _ = await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static async Task InsertProcessingJobAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        PostgresLifecycleOptions options,
        DateTimeOffset now,
        Guid revisionId,
        Guid processingJobId,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.InsertProcessingJob,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", processingJobId);
        command.Parameters.AddWithValue("revisionId", revisionId);
        command.Parameters.AddWithValue("kind", options.ProcessingKind);
        command.Parameters.AddWithValue("maxAttempts", options.MaxAttempts);
        command.Parameters.AddWithValue("idempotencyKey", commit.IdempotencyKey);
        command.Parameters.AddWithValue("availableAt", now.UtcDateTime);
        _ = await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static async Task UpdateDocumentAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        int revisionNumber,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.UpdateDocument,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("revisionNumber", revisionNumber);
        command.Parameters.AddWithValue("documentId", commit.DocumentId);
        command.Parameters.AddWithValue("workspaceId", commit.WorkspaceId);
        if (await command.ExecuteNonQueryAsync(cancellationToken) != 1)
        {
            throw new InvalidDataException("Locked document update did not affect exactly one row.");
        }
    }

    private static async Task InsertOutboxAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        DateTimeOffset now,
        Guid revisionId,
        Guid processingJobId,
        CancellationToken cancellationToken
    )
    {
        var payload = JsonSerializer.Serialize(
            new
            {
                commit.WorkspaceId,
                commit.DocumentId,
                RevisionId = revisionId,
                ProcessingJobId = processingJobId,
                commit.StoredObject.Sha256,
                ManifestSha256 = commit.Manifest.Sha256,
            },
            JsonOptions
        );
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.InsertOutbox,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", Guid.NewGuid());
        command.Parameters.AddWithValue("eventKey", $"revision:{revisionId:D}");
        command.Parameters.AddWithValue("aggregateId", commit.DocumentId);
        command.Parameters.AddWithValue("payloadJson", payload);
        command.Parameters.AddWithValue("createdAt", now.UtcDateTime);
        command.Parameters.AddWithValue("availableAt", now.UtcDateTime);
        _ = await command.ExecuteNonQueryAsync(cancellationToken);
    }
}
