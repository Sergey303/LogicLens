using System.Data;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Npgsql;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Postgres;

public sealed class PostgresDocumentLifecycleRepository : IDocumentLifecycleRepository
{
    private readonly NpgsqlDataSource _dataSource;
    private readonly PostgresLifecycleOptions _options;
    private readonly TimeProvider _timeProvider;

    public PostgresDocumentLifecycleRepository(
        NpgsqlDataSource dataSource,
        PostgresLifecycleOptions? options = null,
        TimeProvider? timeProvider = null
    )
    {
        _dataSource = dataSource ?? throw new ArgumentNullException(nameof(dataSource));
        _options = options ?? new PostgresLifecycleOptions();
        _options.Validate();
        _timeProvider = timeProvider ?? TimeProvider.System;
    }

    public async Task<UploadCompletionResult?> FindUploadCompletionAsync(
        Guid workspaceId,
        string idempotencyKey,
        CancellationToken cancellationToken
    )
    {
        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        return await PostgresLifecycleReader.FindCompletionAsync(
            connection,
            transaction: null,
            workspaceId,
            idempotencyKey,
            cancellationToken
        );
    }

    public async Task<UploadCompletionResult> CommitUploadAndEnqueueProcessingAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(commit);
        try
        {
            return await CommitCoreAsync(commit, cancellationToken);
        }
        catch (PostgresException exception)
            when (exception.SqlState == PostgresErrorCodes.UniqueViolation)
        {
            var existing = await FindUploadCompletionAsync(
                commit.WorkspaceId,
                commit.IdempotencyKey,
                cancellationToken
            );
            return existing
                ?? throw new InvalidDataException(
                    "PostgreSQL unique conflict did not resolve to the idempotent completion.",
                    exception
                );
        }
    }

    private async Task<UploadCompletionResult> CommitCoreAsync(
        UploadCompletionCommit commit,
        CancellationToken cancellationToken
    )
    {
        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        await using var transaction = await connection.BeginTransactionAsync(
            IsolationLevel.ReadCommitted,
            cancellationToken
        );
        var existing = await PostgresLifecycleReader.FindCompletionAsync(
            connection,
            transaction,
            commit.WorkspaceId,
            commit.IdempotencyKey,
            cancellationToken
        );
        if (existing is not null)
        {
            return existing;
        }

        var currentRevision = await PostgresLifecycleReader.LockDocumentAsync(
            connection,
            transaction,
            commit,
            cancellationToken
        );
        var candidateStoredObjectId = Guid.NewGuid();
        var storedObjectId = await PostgresLifecycleReader.InsertStoredObjectAsync(
            connection,
            transaction,
            commit,
            candidateStoredObjectId,
            cancellationToken
        ) ?? await PostgresLifecycleReader.FindAndValidateStoredObjectAsync(
            connection,
            transaction,
            commit,
            cancellationToken
        );

        var revisionId = Guid.NewGuid();
        var processingJobId = Guid.NewGuid();
        var revisionNumber = checked(currentRevision + 1);
        var now = _timeProvider.GetUtcNow();
        await PostgresLifecycleWriter.WriteAsync(
            connection,
            transaction,
            commit,
            _options,
            now,
            storedObjectId,
            revisionId,
            revisionNumber,
            processingJobId,
            cancellationToken
        );
        await transaction.CommitAsync(cancellationToken);

        return new UploadCompletionResult(
            commit.WorkspaceId,
            commit.DocumentId,
            revisionId,
            revisionNumber,
            storedObjectId,
            processingJobId,
            commit.Manifest.Sha256,
            false
        );
    }
}
