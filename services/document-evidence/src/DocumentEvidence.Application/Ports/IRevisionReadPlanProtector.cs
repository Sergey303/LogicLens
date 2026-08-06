using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

public interface IRevisionReadPlanProtector
{
    string Protect(RevisionReadPlanPayload payload);

    RevisionReadPlanPayload Unprotect(string token);
}
