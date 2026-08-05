using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresOutboxWriter
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public static async Task InsertRevisionCreatedAsync(
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
