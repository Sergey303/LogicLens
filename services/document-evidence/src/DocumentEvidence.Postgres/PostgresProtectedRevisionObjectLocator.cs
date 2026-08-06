using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

public sealed class PostgresProtectedRevisionObjectLocator : IProtectedRevisionObjectLocator
{
    private const string FindRevision = """
        SELECT d."WorkspaceId", d."Id", r."Id", r."RevisionNumber",
               o."Sha256", o."SizeBytes", o."MediaType", d."IsRevoked",
               r."RevisionNumber" <> d."CurrentRevisionNumber" AS "IsSuperseded"
        FROM "DocumentRevisions" r
        JOIN "Documents" d ON d."Id" = r."DocumentId"
        JOIN "StoredObjects" o ON o."Id" = r."StoredObjectId"
        WHERE d."WorkspaceId" = @workspaceId
          AND r."Id" = @revisionId;
        """;

    private readonly NpgsqlDataSource _dataSource;

    public PostgresProtectedRevisionObjectLocator(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource ?? throw new ArgumentNullException(nameof(dataSource));
    }

    public async Task<ProtectedRevisionObject?> FindAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        await using var command = _dataSource.CreateCommand(FindRevision);
        command.Parameters.AddWithValue("workspaceId", workspaceId);
        command.Parameters.AddWithValue("revisionId", revisionId);
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }
        return new ProtectedRevisionObject(
            reader.GetGuid(0),
            reader.GetGuid(1),
            reader.GetGuid(2),
            reader.GetInt32(3),
            reader.GetString(4),
            reader.GetInt64(5),
            reader.GetString(6),
            reader.GetBoolean(7),
            reader.GetBoolean(8)
        );
    }
}
