using System.Collections.Concurrent;
using KnowledgePilot.LogicLens.DocumentEvidence.Api;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;
using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoDocumentEvidenceOperations : IDocumentEvidenceApiOperations
{
    private readonly ConcurrentDictionary<(Guid, Guid), DocumentMetadataDto> _documents = new();
    private readonly DemoPdfRevisionProcessor _processor;
    private readonly SecureDocumentUploadService _uploads;

    public DemoDocumentEvidenceOperations(string objectRoot)
    {
        var objects = new LocalImmutableObjectStore(new LocalObjectStoreOptions(objectRoot));
        var repository = new DemoLifecycleRepository();
        _processor = new DemoPdfRevisionProcessor(objects, repository);
        _uploads = new SecureDocumentUploadService(
            new DocumentUploadService(objects, repository),
            new DemoUploadAuthorizationPolicy(),
            new InMemoryUploadQuotaGate(),
            new DemoUploadAuditSink()
        );
    }

    public async Task<UploadRevisionDto> UploadRevisionAsync(
        UploadRevisionRequest request,
        CancellationToken cancellationToken
    )
    {
        if (!string.Equals(request.MediaType, UploadMediaSignature.Pdf, StringComparison.Ordinal))
        {
            throw new DocumentEvidenceApiException(
                415,
                "unsupported-media",
                "ENG-148 accepts PDF only."
            );
        }
        var secured = await _uploads.CompleteAsync(
            new SecureUploadCommand(
                request.ActorId,
                request.WorkspaceId,
                request.DocumentId,
                request.DisplayName,
                request.IdempotencyKey,
                request.MediaType,
                request.SourceKind,
                "poppler-bbox-layout",
                "runtime",
                request.DeclaredLength,
                request.Content
            ),
            cancellationToken
        );
        var completion = secured.Completion;
        await _processor.ProcessAsync(completion.RevisionId, cancellationToken);
        _documents[(request.WorkspaceId, request.DocumentId)] = Metadata(request, secured);
        return new UploadRevisionDto(
            completion.WorkspaceId,
            completion.DocumentId,
            completion.RevisionId,
            completion.RevisionNumber,
            completion.ProcessingJobId,
            completion.ManifestSha256,
            secured.DisplayName,
            "Ready",
            completion.Replayed
        );
    }

    public Task<DocumentMetadataDto?> GetDocumentAsync(
        Guid actorId,
        Guid workspaceId,
        Guid documentId,
        CancellationToken cancellationToken
    )
    {
        DemandActor(actorId, cancellationToken);
        _documents.TryGetValue((workspaceId, documentId), out var result);
        return Task.FromResult(result);
    }

    public Task<IReadOnlyList<DocumentFragmentDto>> ListFragmentsAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        DemandActor(actorId, cancellationToken);
        return Task.FromResult(_processor.List(workspaceId, revisionId));
    }

    private static DocumentMetadataDto Metadata(
        UploadRevisionRequest request,
        SecureUploadResult result
    )
    {
        return new DocumentMetadataDto(
            request.WorkspaceId,
            request.DocumentId,
            result.DisplayName,
            request.MediaType,
            request.SourceKind,
            "Ready",
            result.Completion.RevisionNumber,
            false
        );
    }

    private static void DemandActor(Guid actorId, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (actorId == Guid.Empty)
        {
            throw new UnauthorizedAccessException();
        }
    }
}
