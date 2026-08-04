using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Npgsql;
using NpgsqlTypes;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

public sealed class PostgresProcessingCompletionRepository : IProcessingCompletionRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public PostgresProcessingCompletionRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource ?? throw new ArgumentNullException(nameof(dataSource));
    }

    public async Task<bool> TryCompleteAsync(
        ProcessingJobSnapshot expectedJob,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    )
    {
        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        await using var transaction = await connection.BeginTransactionAsync(cancellationToken);
        if (!await ClaimCompletionAsync(connection, transaction, expectedJob, completion, cancellationToken))
        {
            await transaction.RollbackAsync(cancellationToken);
            return false;
        }

        await UpdateRevisionAsync(connection, transaction, completion, cancellationToken);
        foreach (var fragment in completion.Fragments)
        {
            await InsertFragmentAsync(connection, transaction, fragment, cancellationToken);
        }
        await PostgresProcessingCompletionOutbox.InsertAsync(
            connection,
            transaction,
            expectedJob.JobId,
            completion,
            cancellationToken
        );
        await transaction.CommitAsync(cancellationToken);
        return true;
    }

    private static async Task<bool> ClaimCompletionAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        ProcessingJobSnapshot expected,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresProcessingCompletionSql.ClaimCompletion,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("jobId", expected.JobId);
        command.Parameters.AddWithValue("revisionId", completion.RevisionId);
        command.Parameters.AddWithValue("expectedState", expected.State.ToString());
        command.Parameters.AddWithValue("expectedAttempt", expected.Attempt);
        command.Parameters.AddWithValue("expectedAvailableAt", expected.AvailableAt.UtcDateTime);
        AddNullable(command, "expectedLeaseToken", NpgsqlDbType.Uuid, expected.LeaseToken);
        AddNullable(
            command,
            "expectedLeaseUntil",
            NpgsqlDbType.TimestampTz,
            expected.LeaseUntil?.UtcDateTime
        );
        AddNullable(command, "expectedLastError", NpgsqlDbType.Text, expected.LastError);
        return await command.ExecuteNonQueryAsync(cancellationToken) == 1;
    }

    private static async Task UpdateRevisionAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        ProcessingCompletionPayload completion,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresProcessingCompletionSql.UpdateRevision,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("revisionId", completion.RevisionId);
        command.Parameters.AddWithValue("adapter", completion.Manifest.Adapter);
        command.Parameters.AddWithValue("adapterVersion", completion.Manifest.AdapterVersion);
        command.Parameters.AddWithValue("manifestHash", completion.Manifest.ManifestSha256);
        command.Parameters.AddWithValue("manifestJson", completion.Manifest.ManifestJson);
        if (await command.ExecuteNonQueryAsync(cancellationToken) != 1)
        {
            throw new InvalidOperationException("Processing revision no longer exists.");
        }
    }

    private static async Task InsertFragmentAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        ProcessingFragmentWrite fragment,
        CancellationToken cancellationToken
    )
    {
        await using var command = new NpgsqlCommand(
            PostgresProcessingCompletionSql.InsertFragment,
            connection,
            transaction
        );
        command.Parameters.AddWithValue("id", fragment.FragmentId);
        command.Parameters.AddWithValue("revisionId", fragment.RevisionId);
        command.Parameters.AddWithValue("sequence", fragment.Sequence);
        command.Parameters.AddWithValue("kind", fragment.Kind);
        command.Parameters.AddWithValue("anchorJson", fragment.AnchorJson);
        command.Parameters.AddWithValue("text", fragment.Text);
        command.Parameters.AddWithValue("contentHash", fragment.ContentHash);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static void AddNullable(
        NpgsqlCommand command,
        string name,
        NpgsqlDbType type,
        object? value
    )
    {
        command.Parameters.AddWithValue(name, type, value ?? DBNull.Value);
    }
}
