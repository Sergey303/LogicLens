using System.Collections.Concurrent;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.LocalStorage;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal sealed class DemoPdfRevisionProcessor
{
    private const string SourceId = "document-evidence-pdf";
    private readonly ConcurrentDictionary<Guid, IReadOnlyList<DocumentFragmentDto>> _fragments = new();
    private readonly ConcurrentDictionary<Guid, Guid> _revisionWorkspaces = new();
    private readonly LocalImmutableObjectStore _objects;
    private readonly PdfPopplerAdapter _pdf;
    private readonly DemoLifecycleRepository _repository;

    public DemoPdfRevisionProcessor(
        LocalImmutableObjectStore objects,
        DemoLifecycleRepository repository
    )
    {
        _objects = objects;
        _repository = repository;
        _pdf = new PdfPopplerAdapter(new SystemPdfProcessRunner());
    }

    public async Task ProcessAsync(Guid revisionId, CancellationToken cancellationToken)
    {
        if (_fragments.ContainsKey(revisionId))
        {
            return;
        }
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

    public IReadOnlyList<DocumentFragmentDto> List(Guid workspaceId, Guid revisionId)
    {
        if (!_revisionWorkspaces.TryGetValue(revisionId, out var owner) || owner != workspaceId)
        {
            throw new UnauthorizedAccessException();
        }
        return _fragments.TryGetValue(revisionId, out var result) ? result : [];
    }
}
