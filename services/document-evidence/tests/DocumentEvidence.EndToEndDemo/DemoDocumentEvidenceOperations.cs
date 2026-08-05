using System.Collections.Concurrent;
using KnowledgePilot.LogicLens.DocumentEvidence.Api;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;
using KnowledgePilot.LogicLens.DocumentEvidence.Security;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoDocumentEvidenceOperations : IDocumentEvidenceApiOperations
{
    private const string SourceId = "document-evidence-pdf";
    private readonly ConcurrentDictionary<(Guid, Guid), DocumentMetadataDto> _documents = new();
    private readonly ConcurrentDictionary<Guid, IReadOnlyList<DocumentFragmentDto>> _fragments = new();
    private readonly ConcurrentDictionary<Guid, Guid> _revisionWorkspaces = new();
    private readonly LocalImmutableObjectStore _objects;
    private readonly PdfPopplerAdapter _pdf;
    private readonly DemoLifecycleRepository _repository;
    private readonly SecureDocumentUploadService _uploads;

    public DemoDocumentEvidenceOperations(string objectRoot)
    {
        _objects = new LocalImmutableObjectStore(new LocalObjectStoreOptions(objectRoot));
        _repository = new DemoLifecycleRepository();
        _pdf = new PdfPopplerAdapter(new SystemPdfProcessRunner());
        _uploads = new SecureDocumentUploadService(
            new DocumentUploadService(_objects, _repository),
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
            throw new DocumentEvidenceApiException(415, "unsupported-media", "ENG-148 accepts PDF only.");
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
        if (!_fragments.ContainsKey(completion.RevisionId))
        {
            await ParseRevisionAsync(completion.RevisionId, cancellationToken);
        }
        _documents[(request.WorkspaceId, request.DocumentId)] = new DocumentMetadataDto(
            request.WorkspaceId,
            request.DocumentId,
            secured.DisplayName,
            request.MediaType,
            request.SourceKind,
            "Ready",
            completion.RevisionNumber,
            false
        );
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
        if (!_revisionWorkspaces.TryGetValue(revisionId, out var owner) || owner != workspaceId)
        {
            throw new UnauthorizedAccessException();
        }
        return Task.FromResult(
            _fragments.TryGetValue(revisionId, out var result)
                ? result
                : (IReadOnlyList<DocumentFragmentDto>)[]
        );
    }

    private async Task ParseRevisionAsync(Guid revisionId, CancellationToken cancellationToken)
    {
        var commit = _repository.GetCommit(revisionId);
        await using var source = await _objects.OpenReadAsync(
            commit.StoredObject.Sha256,
            cancellationToken
        );
        var extraction = await _pdf.ExtractAsync(
            source,
            new PdfExtractionRequest(
                SourceId,
                "urn:logiclens:eng-148:demo.pdf",
                commit.StoredObject.SizeBytes,
                commit.StoredObject.Sha256
            ),
            cancellationToken
        );
        _fragments[revisionId] = DemoFragmentMapper.Map(extraction, revisionId);
        _revisionWorkspaces[revisionId] = commit.WorkspaceId;
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
