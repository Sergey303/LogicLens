using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application;

public sealed class DocumentUploadService
{
    private readonly IDocumentLifecycleRepository _repository;
    private readonly IImmutableObjectStore _store;

    public DocumentUploadService(
        IImmutableObjectStore store,
        IDocumentLifecycleRepository repository
    )
    {
        _store = store;
        _repository = repository;
    }

    public async Task<UploadCompletionResult> CompleteAsync(
        CompleteUploadCommand command,
        CancellationToken cancellationToken = default
    )
    {
        ValidateCommand(command);
        var existing = await _repository.FindUploadCompletionAsync(
            command.WorkspaceId,
            command.IdempotencyKey,
            cancellationToken
        );
        if (existing is not null)
        {
            DemandResultIdentity(existing, command, expectedManifestHash: null);
            return existing with { Replayed = true };
        }

        var storedObject = await _store.PutAsync(command.Content, cancellationToken);
        var manifest = RevisionManifestFactory.Create(
            storedObject,
            command.MediaType,
            command.SourceKind,
            command.Adapter,
            command.AdapterVersion
        );
        var commit = new UploadCompletionCommit(
            command.WorkspaceId,
            command.DocumentId,
            command.IdempotencyKey,
            storedObject,
            manifest
        );
        var result = await _repository.CommitUploadAndEnqueueProcessingAsync(
            commit,
            cancellationToken
        );
        DemandResultIdentity(result, command, manifest.Sha256);
        return result;
    }

    private static void ValidateCommand(CompleteUploadCommand command)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.WorkspaceId == Guid.Empty || command.DocumentId == Guid.Empty)
        {
            throw new ArgumentException("Workspace and document identifiers are required.");
        }
        if (!command.Content.CanRead)
        {
            throw new ArgumentException("Upload content stream must be readable.", nameof(command));
        }
        DemandIdempotencyKey(command.IdempotencyKey);
    }

    private static void DemandIdempotencyKey(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        if (value.Length > 160 || value.Any(character => !IsIdempotencyCharacter(character)))
        {
            throw new ArgumentException(
                "Idempotency key must use 1-160 letters, digits, '.', '_', ':', or '-'.",
                nameof(value)
            );
        }
    }

    private static bool IsIdempotencyCharacter(char character)
    {
        return char.IsAsciiLetterOrDigit(character) || character is '.' or '_' or ':' or '-';
    }

    private static void DemandResultIdentity(
        UploadCompletionResult result,
        CompleteUploadCommand command,
        string? expectedManifestHash
    )
    {
        if (result.WorkspaceId != command.WorkspaceId || result.DocumentId != command.DocumentId)
        {
            throw new InvalidDataException("Idempotent upload result belongs to another document.");
        }
        if (expectedManifestHash is not null
            && !string.Equals(result.ManifestSha256, expectedManifestHash, StringComparison.Ordinal))
        {
            throw new InvalidDataException("Idempotency key resolved to a different revision manifest.");
        }
    }
}
