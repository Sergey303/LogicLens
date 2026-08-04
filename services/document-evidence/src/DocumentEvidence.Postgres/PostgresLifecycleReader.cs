using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

internal static class PostgresLifecycleReader
{
    public static async Task<UploadCompletionResult?> FindCompletionAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction? transaction,
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.FindCompletion,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("workspaceId", workspaceId);
        command.Parameters.AddWithValue("idempotencyKey", idempotencyKey);
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        var manifestHash = reader.IsDBNull(6)
            ? throw new InvalidDataException("Persisted revision is missing its manifest hash.")
            : reader.GetString(6);
        return new UploadCompletionResult(
            reader.GetGuid(0),
            reader.GetGuid(1),
            reader.GetGuid(2),
            reader.GetInt32(3),
            reader.GetGuid(4),
            reader.GetGuid(5),
            manifestHash,
            true
        );
    }

    public static async Task<int> LockDocumentAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.LockDocument,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("documentId", commit.DocumentId);
        command.Parameters.AddWithValue("workspaceId", commit.WorkspaceId);
        var value = await command.ExecuteScalarAsync(cancellationToken);
        return value switch
        {
            int revisionNumber => revisionNumber,
            null or DBNull => throw new InvalidOperationException(
                "Document does not exist, belongs to another workspace, or is revoked."
            ),
            _ => throw new InvalidDataException("Document revision number has an unexpected type."),
        };
    }

    public static async Task<Guid?> InsertStoredObjectAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        Guid candidateId,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.InsertStoredObject,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", candidateId);
        command.Parameters.AddWithValue("sha256", commit.StoredObject.Sha256);
        command.Parameters.AddWithValue("storageKey", commit.StoredObject.ObjectKey);
        command.Parameters.AddWithValue("sizeBytes", commit.StoredObject.SizeBytes);
        command.Parameters.AddWithValue("mediaType", commit.Manifest.MediaType);
        var value = await command.ExecuteScalarAsync(cancellationToken);
        return value is Guid id ? id : null;
    }

    public static async Task<Guid> FindAndValidateStoredObjectAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresLifecycleSql.FindStoredObject,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("sha256", commit.StoredObject.Sha256);
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            throw new InvalidDataException("Stored object conflict did not resolve to a row.");
        }
        if (reader.GetString(1) != commit.StoredObject.ObjectKey
            || reader.GetInt64(2) != commit.StoredObject.SizeBytes
            || reader.GetString(3) != commit.Manifest.MediaType)
        {
            throw new InvalidDataException("Stored object hash resolved to conflicting metadata.");
        }
        return reader.GetGuid(0);
    }
}
