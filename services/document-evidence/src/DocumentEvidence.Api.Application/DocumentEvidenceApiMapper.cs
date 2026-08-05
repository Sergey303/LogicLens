using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Api.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Api.Application;

internal static class DocumentEvidenceApiMapper
{
    public static DocumentMetadataDto Document(DocumentSummary source) => new(
        source.Key.WorkspaceId,
        source.Key.DocumentId,
        source.DisplayName,
        source.MediaType,
        source.SourceKind,
        source.State,
        source.CurrentRevisionNumber,
        source.IsRevoked
    );

    public static DocumentFragmentDto Fragment(FragmentSummary source)
    {
        JsonElement anchor;
        try
        {
            using var document = JsonDocument.Parse(source.AnchorJson);
            anchor = document.RootElement.Clone();
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException(
                $"Stored fragment anchor is invalid JSON: {source.FragmentId:D}",
                exception
            );
        }
        return new DocumentFragmentDto(
            source.FragmentId,
            source.RevisionId,
            source.Sequence,
            source.Kind,
            new FragmentAnchorDto(source.Kind, anchor),
            source.Text,
            source.ContentHash
        );
    }
}
