using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresProcessingCompletionOutbox
{
    public static async Task InsertAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        Guid jobId,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresProcessingCompletionSql.InsertOutbox,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", Guid.NewGuid());
        command.Parameters.AddWithValue(
            "eventKey",
            $"revision:{completion.RevisionId}:processed:{completion.Manifest.ManifestSha256}"
        );
        command.Parameters.AddWithValue("revisionId", completion.RevisionId);
        command.Parameters.AddWithValue(
            "payloadJson",
            JsonSerializer.Serialize(new {
                jobId,
                revisionId = completion.RevisionId,
                completion.Manifest.Adapter,
                completion.Manifest.AdapterVersion,
                completion.Manifest.ManifestSha256,
                fragmentCount = completion.Fragments.Count,
            })
        );
        command.Parameters.AddWithValue("completedAt", completion.CompletedAt.UtcDateTime);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }
}
