using KnowledgePilot.LogicLens.DocumentEvidence.Api;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Microsoft.AspNetCore.Http;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Application;

public sealed class DocumentEvidenceReadPlanApiOperations :
    IDocumentEvidenceReadPlanApiOperations
{
    private readonly RevisionReadPlanService _plans;
    private readonly IRevisionReadPlanProtector _protector;

    public DocumentEvidenceReadPlanApiOperations(
        RevisionReadPlanService plans,
        IRevisionReadPlanProtector protector
    )
    {
        _plans = plans ?? throw new ArgumentNullException(nameof(plans));
        _protector = protector ?? throw new ArgumentNullException(nameof(protector));
    }

    public async Task<ReadPlanDto> IssueReadPlanAsync(
        Guid actorId,
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var plan = await _plans.IssueAsync(
                new IssueRevisionReadPlanCommand(actorId, workspaceId, revisionId),
                cancellationToken
            );
            return new ReadPlanDto(
                plan.PlanId,
                plan.WorkspaceId,
                plan.DocumentId,
                plan.RevisionId,
                plan.RevisionNumber,
                plan.ExpiresAtUtc,
                plan.MediaType,
                plan.SizeBytes,
                plan.ObjectSha256,
                plan.Token
            );
        }
        catch (Exception exception) when (TryMap(exception, out var mapped))
        {
            throw mapped;
        }
    }

    public async Task<RevisionReadContent> OpenReadPlanAsync(
        Guid actorId,
        string token,
        CancellationToken cancellationToken
    )
    {
        try
        {
            var payload = _protector.Unprotect(token);
            var stream = await _plans.OpenAsync(
                new ExecuteRevisionReadPlanCommand(actorId, token),
                cancellationToken
            );
            return new RevisionReadContent(
                stream,
                payload.MediaType,
                payload.SizeBytes,
                payload.ObjectSha256
            );
        }
        catch (Exception exception) when (TryMap(exception, out var mapped))
        {
            throw mapped;
        }
    }

    private static bool TryMap(Exception exception, out DocumentEvidenceApiException mapped)
    {
        mapped = exception switch
        {
            UnauthorizedAccessException => new DocumentEvidenceApiException(
                StatusCodes.Status403Forbidden,
                "read-plan-denied",
                "The revision read plan is invalid or no longer authorized."
            ),
            FileNotFoundException => new DocumentEvidenceApiException(
                StatusCodes.Status404NotFound,
                "revision-not-found",
                "The requested revision was not found."
            ),
            InvalidDataException or ArgumentException => new DocumentEvidenceApiException(
                StatusCodes.Status400BadRequest,
                "invalid-read-plan-request",
                "The revision read plan request is invalid."
            ),
            _ => null!,
        };
        return mapped is not null;
    }
}
