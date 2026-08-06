using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.ContractTests;

internal sealed class FakeReadPlanApiOperations : IDocumentEvidenceReadPlanApiOperations
{
    public const string Token = "signed.read.plan.token";
    public static readonly byte[] Bytes = [1, 2, 3, 4];
    public Guid? IssuedActorId { get; private set; }
    public Guid? IssuedWorkspaceId { get; private set; }
    public Guid? IssuedRevisionId { get; private set; }
    public Guid? OpenedActorId { get; private set; }
    public string? OpenedToken { get; private set; }

    public Task<ReadPlanDto> IssueReadPlanAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        IssuedActorId = actorId;
        IssuedWorkspaceId = workspaceId;
        IssuedRevisionId = revisionId;
        return Task.FromResult(new ReadPlanDto(
            Guid.Parse("44444444-4444-4444-4444-444444444444"),
            workspaceId,
            Guid.Parse("55555555-5555-5555-5555-555555555555"),
            revisionId,
            1,
            DateTimeOffset.Parse("2026-08-07T00:30:00Z"),
            "application/pdf",
            Bytes.LongLength,
            new string('c', 64),
            Token
        ));
    }

    public Task<RevisionReadContent> OpenReadPlanAsync(
        Guid actorId,
        string token,
        CancellationToken cancellationToken
    )
    {
        OpenedActorId = actorId;
        OpenedToken = token;
        return Task.FromResult(new RevisionReadContent(
            new MemoryStream(Bytes, writable: false),
            "application/pdf",
            Bytes.LongLength,
            new string('c', 64)
        ));
    }
}
