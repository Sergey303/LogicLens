using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

internal static class GeneratedContractMapper
{
    public static DocumentSummary MapDocument(GeneratedDocumentDto document)
    {
        var key = new DocumentKey(document.WorkspaceId, document.Id);
        return new DocumentSummary(
            key,
            document.DisplayName,
            document.MediaType,
            document.SourceKind,
            document.State,
            document.CurrentRevisionNumber,
            document.IsRevoked
        );
    }

    public static FragmentSummary MapFragment(GeneratedDocumentFragmentDto fragment)
    {
        return new FragmentSummary(
            fragment.Id,
            fragment.DocumentRevisionId,
            fragment.Sequence,
            fragment.Kind,
            fragment.AnchorJson,
            fragment.Text,
            fragment.ContentHash
        );
    }
}
