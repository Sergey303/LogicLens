using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Security;

public sealed class SecureDocumentUploadService
{
    private readonly IUploadAuditSink _audit;
    private readonly IUploadAuthorizationPolicy _authorization;
    private readonly DocumentUploadService _inner;
    private readonly SecureUploadOptions _options;
    private readonly IUploadQuotaGate _quotas;
    private readonly TimeProvider _timeProvider;

    public SecureDocumentUploadService(
        DocumentUploadService inner,
        IUploadAuthorizationPolicy authorization,
        IUploadQuotaGate quotas,
        IUploadAuditSink audit,
        SecureUploadOptions? options = null,
        TimeProvider? timeProvider = null
    )
    {
        _inner = inner;
        _authorization = authorization;
        _quotas = quotas;
        _audit = audit;
        _options = options ?? new SecureUploadOptions();
        _timeProvider = timeProvider ?? TimeProvider.System;
        if (_options.MaxUploadBytes < 1 || _options.MaxDisplayNameLength < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(options));
        }
    }

    public async Task<SecureUploadResult> CompleteAsync(
        SecureUploadCommand command,
        CancellationToken cancellationToken = default
    )
    {
        ValidateIdentity(command);
        long observedBytes = 0;
        try
        {
            await _authorization.DemandWorkspaceUploadAsync(
                command.ActorId,
                command.WorkspaceId,
                cancellationToken
            );
            await _quotas.DemandRequestAsync(
                command.ActorId,
                command.WorkspaceId,
                cancellationToken
            );
            var displayName = UploadDisplayName.Normalize(
                command.DisplayName,
                _options.MaxDisplayNameLength
            );
            var bytes = await BoundedUploadBuffer.ReadAsync(
                command.Content,
                command.DeclaredLength,
                _options.MaxUploadBytes,
                cancellationToken
            );
            observedBytes = bytes.LongLength;
            UploadMediaSignature.DemandMatch(command.MediaType, bytes);
            await _quotas.DemandBytesAsync(
                command.WorkspaceId,
                observedBytes,
                cancellationToken
            );
            await using var content = new MemoryStream(bytes, writable: false);
            var completion = await _inner.CompleteAsync(
                ToCompletionCommand(command, content),
                cancellationToken
            );
            await RecordAsync(command, observedBytes, "accepted", cancellationToken);
            return new SecureUploadResult(displayName, completion);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception exception) when (IsExpectedRejection(exception))
        {
            await RecordAsync(
                command,
                observedBytes,
                RejectionOutcome(exception),
                cancellationToken
            );
            throw;
        }
    }

    private static CompleteUploadCommand ToCompletionCommand(
        SecureUploadCommand command,
        Stream content
    ) => new(
        command.WorkspaceId,
        command.DocumentId,
        command.IdempotencyKey,
        command.MediaType,
        command.SourceKind,
        command.Adapter,
        command.AdapterVersion,
        content
    );

    private ValueTask RecordAsync(
        SecureUploadCommand command,
        long sizeBytes,
        string outcome,
        CancellationToken cancellationToken
    ) => _audit.RecordAsync(
        new UploadAuditRecord(
            "document.upload.completed",
            command.ActorId,
            command.WorkspaceId,
            command.DocumentId,
            command.MediaType,
            sizeBytes,
            outcome,
            _timeProvider.GetUtcNow()
        ),
        cancellationToken
    );

    private static void ValidateIdentity(SecureUploadCommand command)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.ActorId == Guid.Empty
            || command.WorkspaceId == Guid.Empty
            || command.DocumentId == Guid.Empty)
        {
            throw new ArgumentException("Actor, workspace, and document identifiers are required.");
        }
    }

    private static bool IsExpectedRejection(Exception exception) => exception is
        ArgumentException or InvalidDataException or UnauthorizedAccessException
        or UploadQuotaExceededException;

    private static string RejectionOutcome(Exception exception) => exception switch
    {
        UploadQuotaExceededException quota => $"rejected:{quota.QuotaCode}",
        UnauthorizedAccessException => "rejected:access-denied",
        InvalidDataException => "rejected:invalid-content",
        _ => "rejected:invalid-request",
    };
}
