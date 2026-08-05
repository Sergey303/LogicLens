using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Npgsql;
using NpgsqlTypes;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

public sealed class PostgresProcessingJobRepository : IProcessingJobRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public PostgresProcessingJobRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource ?? throw new ArgumentNullException(nameof(dataSource));
    }

    public async Task<ProcessingJobSnapshot?> FindNextAvailableAsync(
        DateTimeOffset now,
        CancellationToken cancellationToken
    )
    {
        await using var command = _dataSource.CreateCommand(
            PostgresProcessingJobSql.FindNextAvailable
        );
        command.Parameters.AddWithValue("now", now.UtcDateTime);
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new ProcessingJobSnapshot(
            reader.GetGuid(0),
            ParseState(reader.GetString(1)),
            reader.GetInt32(2),
            reader.GetInt32(3),
            ReadTimestamp(reader, 4),
            reader.IsDBNull(5) ? null : reader.GetGuid(5),
            reader.IsDBNull(6) ? null : ReadTimestamp(reader, 6),
            reader.IsDBNull(7) ? null : reader.GetString(7)
        );
    }

    public async Task<bool> CompareExchangeAsync(
        ProcessingJobSnapshot expected,
        ProcessingJobSnapshot replacement,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(expected);
        ArgumentNullException.ThrowIfNull(replacement);
        if (expected.JobId != replacement.JobId
            || expected.MaxAttempts != replacement.MaxAttempts)
        {
            throw new ArgumentException("Processing job CAS cannot change identity or MaxAttempts.");
        }

        await using var command = _dataSource.CreateCommand(
            PostgresProcessingJobSql.CompareExchange
        );
        command.Parameters.AddWithValue("id", expected.JobId);
        command.Parameters.AddWithValue("expectedState", expected.State.ToString());
        command.Parameters.AddWithValue("expectedAttempt", expected.Attempt);
        command.Parameters.AddWithValue("expectedAvailableAt", expected.AvailableAt.UtcDateTime);
        AddNullableGuid(command, "expectedLeaseToken", expected.LeaseToken);
        AddNullableTimestamp(command, "expectedLeaseUntil", expected.LeaseUntil);
        AddNullableText(command, "expectedLastError", expected.LastError);
        command.Parameters.AddWithValue("replacementState", replacement.State.ToString());
        command.Parameters.AddWithValue("replacementAttempt", replacement.Attempt);
        command.Parameters.AddWithValue(
            "replacementAvailableAt",
            replacement.AvailableAt.UtcDateTime
        );
        AddNullableGuid(command, "replacementLeaseToken", replacement.LeaseToken);
        AddNullableTimestamp(command, "replacementLeaseUntil", replacement.LeaseUntil);
        AddNullableText(command, "replacementLastError", replacement.LastError);
        return await command.ExecuteNonQueryAsync(cancellationToken) == 1;
    }

    private static ProcessingJobState ParseState(string value)
    {
        return Enum.TryParse<ProcessingJobState>(value, ignoreCase: false, out var state)
            ? state
            : throw new InvalidDataException($"Unknown persisted processing state '{value}'.");
    }

    private static DateTimeOffset ReadTimestamp(NpgsqlDataReader reader, int ordinal)
    {
        var value = DateTime.SpecifyKind(reader.GetDateTime(ordinal), DateTimeKind.Utc);
        return new DateTimeOffset(value);
    }

    private static void AddNullableGuid(NpgsqlCommand command, string name, Guid? value)
    {
        command.Parameters.AddWithValue(name, NpgsqlDbType.Uuid, value ?? (object)DBNull.Value);
    }

    private static void AddNullableTimestamp(
        NpgsqlCommand command,
        string name,
        DateTimeOffset? value
    )
    {
        command.Parameters.AddWithValue(
            name,
            NpgsqlDbType.TimestampTz,
            value?.UtcDateTime ?? (object)DBNull.Value
        );
    }

    private static void AddNullableText(NpgsqlCommand command, string name, string? value)
    {
        command.Parameters.AddWithValue(name, NpgsqlDbType.Text, value ?? (object)DBNull.Value);
    }
}
