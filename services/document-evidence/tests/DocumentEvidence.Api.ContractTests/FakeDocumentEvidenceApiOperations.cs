using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal sealed class FakeDocumentEvidenceApiOperations : IDocumentEvidenceApiOperations
{
    public UploadRevisionRequest? UploadRequest { get; private set; }

    public async Task<UploadRevisionDto> UploadRevisionAsync(
        UploadRevisionRequest request,
        CancellationToken cancellationToken
    )
    {
        using var output = new MemoryStream();
        await request.Content.CopyToAsync(output, cancellationToken);
        UploadRequest = request with
        {
            Content = new MemoryStream(output.ToArray(), writable: false),
        };
        return new UploadRevisionDto(
            request.WorkspaceId,
            request.DocumentId,
            Guid.Parse("11111111-1111-1111-1111-111111111111"),
            1,
            Guid.Parse("22222222-2222-2222-2222-222222222222"),
            new string('a', 64),
            request.DisplayName,
            "Pending",
            false
        );
    }

    public Task<DocumentMetadataDto?> GetDocumentAsync(
        Guid actorId,
        Guid workspaceId,
        Guid documentId,
        CancellationToken cancellationToken
    ) => Task.FromResult<DocumentMetadataDto?>(new DocumentMetadataDto(
        workspaceId,
        documentId,
        "demo.pdf",
        "application/pdf",
        "Upload",
        "Ready",
        1,
        false
    ));

    public Task<IReadOnlyList<DocumentFragmentDto>> ListFragmentsAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        using var document = JsonDocument.Parse("{\"page\":1,\"blockId\":\"pdf:block-1\"}");
        IReadOnlyList<DocumentFragmentDto> result =
        [
            new DocumentFragmentDto(
                Guid.Parse("33333333-3333-3333-3333-333333333333"),
                revisionId,
                1,
                "pdf-block",
                new FragmentAnchorDto("pdf-block", document.RootElement.Clone()),
                "Rated power: 120 W",
                new string('b', 64)
            ),
        ];
        return Task.FromResult(result);
    }
}
