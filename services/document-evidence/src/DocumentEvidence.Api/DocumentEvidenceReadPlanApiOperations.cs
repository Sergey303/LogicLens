using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api;

public sealed record RevisionReadContent(
    Stream Content,
    string MediaType,
    long SizeBytes,
    string ContentSha256
);

public interface IDocumentEvidenceReadPlanApiOperations
{
    Task<ReadPlanDto> IssueReadPlanAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    );

    Task<RevisionReadContent> OpenReadPlanAsync(
        Guid actorId,
        string token,
        CancellationToken cancellationToken
    );
}
