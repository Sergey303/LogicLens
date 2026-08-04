using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Contracts;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

public sealed class AppForgeGeneratedOperationalStore : IGeneratedOperationalStore
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly HttpClient _httpClient;

    public AppForgeGeneratedOperationalStore(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<DocumentSummary?> FindDocumentAsync(
        DocumentKey key,
        CancellationToken cancellationToken
    )
    {
        var document = await GetOrNullAsync<GeneratedDocumentDto>(
            AppForgeGeneratedRoutes.Document(key.DocumentId),
            cancellationToken
        );
        if (document is null)
        {
            return null;
        }

        DemandDocumentIdentity(document, key);
        return MapDocument(document);
    }

    public async Task<IReadOnlyList<FragmentSummary>> ListFragmentsAsync(
        Guid workspaceId,
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        var revision = await GetOrNullAsync<GeneratedDocumentRevisionDto>(
            AppForgeGeneratedRoutes.Revision(revisionId),
            cancellationToken
        );
        if (revision is null)
        {
            return [];
        }
        if (revision.Id != revisionId)
        {
            throw ContractViolation("Revision response id does not match the requested revision.");
        }

        var document = await GetRequiredAsync<GeneratedDocumentDto>(
            AppForgeGeneratedRoutes.Document(revision.DocumentId),
            cancellationToken
        );
        if (document.Id != revision.DocumentId || document.WorkspaceId != workspaceId)
        {
            throw ContractViolation("Revision resolved outside the authorized workspace.");
        }

        return await ReadAllFragmentsAsync(revisionId, cancellationToken);
    }

    private async Task<IReadOnlyList<FragmentSummary>> ReadAllFragmentsAsync(
        Guid revisionId,
        CancellationToken cancellationToken
    )
    {
        var fragments = new List<FragmentSummary>();
        for (var page = 1; ; page++)
        {
            var result = await GetRequiredAsync<GeneratedListResult<GeneratedDocumentFragmentDto>>(
                AppForgeGeneratedRoutes.FragmentPage(revisionId, page),
                cancellationToken
            );
            if (result.Page != page || result.TotalCount < 0)
            {
                throw ContractViolation("Fragment pagination metadata is inconsistent.");
            }

            foreach (var fragment in result.Items)
            {
                if (fragment.DocumentRevisionId != revisionId)
                {
                    throw ContractViolation("Fragment response crossed the requested revision boundary.");
                }
                fragments.Add(MapFragment(fragment));
            }

            if (fragments.Count >= result.TotalCount)
            {
                return fragments;
            }
            if (result.Items.Count == 0)
            {
                throw ContractViolation("Fragment pagination ended before TotalCount was reached.");
            }
        }
    }

    private async Task<T?> GetOrNullAsync<T>(string route, CancellationToken cancellationToken)
    {
        using var response = await _httpClient.GetAsync(route, cancellationToken);
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<T>(JsonOptions, cancellationToken)
            ?? throw ContractViolation($"Generated API returned an empty JSON body for '{route}'.");
    }

    private async Task<T> GetRequiredAsync<T>(string route, CancellationToken cancellationToken)
    {
        return await GetOrNullAsync<T>(route, cancellationToken)
            ?? throw ContractViolation($"Generated API returned 404 for required resource '{route}'.");
    }

    private static void DemandDocumentIdentity(GeneratedDocumentDto document, DocumentKey key)
    {
        if (document.Id != key.DocumentId || document.WorkspaceId != key.WorkspaceId)
        {
            throw ContractViolation("Document response does not match the requested workspace key.");
        }
    }

    private static DocumentSummary MapDocument(GeneratedDocumentDto document)
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

    private static FragmentSummary MapFragment(GeneratedDocumentFragmentDto fragment)
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

    private static InvalidDataException ContractViolation(string message)
    {
        return new InvalidDataException($"AppForge generated contract violation: {message}");
    }
}
