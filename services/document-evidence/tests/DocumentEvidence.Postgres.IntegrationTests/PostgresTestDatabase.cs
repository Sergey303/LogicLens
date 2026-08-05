using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres.IntegrationTests;

internal sealed class PostgresTestDatabase : IAsyncDisposable
{
    private readonly NpgsqlDataSource _dataSource;

    private PostgresTestDatabase(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public NpgsqlDataSource DataSource => _dataSource;

    public static async Task<PostgresTestDatabase> CreateAsync()
    {
        var connectionString = Environment.GetEnvironmentVariable(
            "DOCUMENT_EVIDENCE_TEST_POSTGRES"
        ) ?? "Host=127.0.0.1;Port=5432;Database=document_evidence;Username=postgres;Password=postgres";
        var database = new PostgresTestDatabase(NpgsqlDataSource.Create(connectionString));
        await database.ResetAsync();
        return database;
    }

    public async Task ResetAsync()
    {
        var sql = await File.ReadAllTextAsync(Path.Combine(AppContext.BaseDirectory, "schema.sql"));
        await ExecuteAsync(sql);
    }

    public async Task SeedDocumentAsync(Guid workspaceId, Guid documentId)
    {
        const string sql = """
            INSERT INTO "Documents"
                ("Id", "WorkspaceId", "DisplayName", "MediaType", "SourceKind",
                 "State", "CurrentRevisionNumber", "IsRevoked")
            VALUES
                (@id, @workspaceId, 'Evidence.pdf', 'application/pdf', 'Upload',
                 'Created', 0, FALSE);
            """;
        await using var command = _dataSource.CreateCommand(sql);
        command.Parameters.AddWithValue("id", documentId);
        command.Parameters.AddWithValue("workspaceId", workspaceId);
        _ = await command.ExecuteNonQueryAsync();
    }

    public async Task ExecuteAsync(string sql)
    {
        await using var command = _dataSource.CreateCommand(sql);
        _ = await command.ExecuteNonQueryAsync();
    }

    public async Task<T> ScalarAsync<T>(string sql)
        where T : notnull
    {
        await using var command = _dataSource.CreateCommand(sql);
        var value = await command.ExecuteScalarAsync();
        return value is T result
            ? result
            : throw new InvalidDataException($"Unexpected scalar result for '{sql}'.");
    }

    public async ValueTask DisposeAsync()
    {
        await _dataSource.DisposeAsync();
    }
}
