#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class DocumentFragmentService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public DocumentFragmentService(DocumentEvidenceOperationalModelDbContext db)
    {
        _db = db;
    }

    public IQueryable<StaffPositionAssignment> ActiveStaffPositionAssignments(Guid userId, DateTime now)
    {
        return _db.StaffPositionAssignments.Where(assignment =>
            assignment.UserId == userId
            && assignment.IsActive
            && assignment.StaffPosition.IsActive
            && assignment.StartsAt <= now
            && (!assignment.EndsAt.HasValue || assignment.EndsAt.Value > now));
    }

    public async Task<ListDocumentFragmentResult> ListAsync(
        ListDocumentFragmentRequest request,
        Func<IQueryable<DocumentFragment>, IQueryable<DocumentFragment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<DocumentFragment> query = _db.DocumentFragments.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListDocumentFragmentResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<DocumentFragment?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<DocumentFragment> query = _db.DocumentFragments;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentFragmentLookupDto>> LookupAsync(
        LookupDocumentFragmentRequest request,
        Func<IQueryable<DocumentFragment>, IQueryable<DocumentFragment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.DocumentFragments.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.KindSearch.Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.Kind);

        return await query
            .Take(take)
            .Select(item => new DocumentFragmentLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Kind,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentFragmentSuggestionDto>> SuggestAsync(
        string field,
        SuggestDocumentFragmentRequest request,
        Func<IQueryable<DocumentFragment>, IQueryable<DocumentFragment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.DocumentFragments.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "kind":
                return await query
                    .Where(item => item.Kind != null)
                    .Where(item => normalizedQuery.Length == 0 || item.KindSearch.Contains(normalizedQuery))
                    .Select(item => item.Kind!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentFragmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "anchorjson":
                return await query
                    .Where(item => item.AnchorJson != null)
                    .Where(item => normalizedQuery.Length == 0 || item.AnchorJsonSearch.Contains(normalizedQuery))
                    .Select(item => item.AnchorJson!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentFragmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "text":
                return await query
                    .Where(item => item.Text != null)
                    .Where(item => normalizedQuery.Length == 0 || item.TextSearch.Contains(normalizedQuery))
                    .Select(item => item.Text!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentFragmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "contenthash":
                return await query
                    .Where(item => item.ContentHash != null)
                    .Where(item => normalizedQuery.Length == 0 || item.ContentHashSearch.Contains(normalizedQuery))
                    .Select(item => item.ContentHash!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentFragmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentFragmentSuggestionDto>();
    }

    public async Task<IReadOnlyList<DocumentFragmentOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<DocumentFragment>, IQueryable<DocumentFragment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.DocumentFragments.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "kind":
                return await query
                    .Where(item => item.Kind != null)
                    .Select(item => item.Kind!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Select(value => new DocumentFragmentOptionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentFragmentOptionDto>();
    }

    public async Task<DocumentFragment> CreateAsync(
        CreateDocumentFragmentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new DocumentFragment
        {
            Id = Guid.NewGuid(),
            DocumentRevisionId = request.DocumentRevisionId,
            Sequence = request.Sequence,
            Kind = request.Kind,
            AnchorJson = request.AnchorJson,
            Text = request.Text,
            ContentHash = request.ContentHash,
            CreationTime = DateTime.UtcNow,
            CreatorId = currentUserId,
            CreatorPositionId = currentAuditPositionId,
            IsDeleted = false,
            KindSearch = NormalizeSearchValue(request.Kind),
            AnchorJsonSearch = NormalizeSearchValue(request.AnchorJson),
            TextSearch = NormalizeSearchValue(request.Text),
            ContentHashSearch = NormalizeSearchValue(request.ContentHash),
        };

        _db.DocumentFragments.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<DocumentFragment> UpdateAsync(
        DocumentFragment entity,
        UpdateDocumentFragmentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.DocumentRevisionId = request.DocumentRevisionId;
        entity.Sequence = request.Sequence;
        entity.Kind = request.Kind;
        entity.AnchorJson = request.AnchorJson;
        entity.Text = request.Text;
        entity.ContentHash = request.ContentHash;
        entity.KindSearch = NormalizeSearchValue(request.Kind);
        entity.AnchorJsonSearch = NormalizeSearchValue(request.AnchorJson);
        entity.TextSearch = NormalizeSearchValue(request.Text);
        entity.ContentHashSearch = NormalizeSearchValue(request.ContentHash);
        entity.LastModificationTime = DateTime.UtcNow;
        entity.LastModifierId = currentUserId;
        entity.LastModifierPositionId = currentAuditPositionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        DocumentFragment entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.IsDeleted = true;
        entity.DeletionTime = DateTime.UtcNow;
        entity.DeleterId = currentUserId;
        entity.DeleterPositionId = currentAuditPositionId;

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        DocumentFragment entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public DocumentFragmentDto ToDto(DocumentFragment entity)
    {
        return new DocumentFragmentDto
        {
            Id = entity.Id,
            DocumentRevisionId = entity.DocumentRevisionId,
            Sequence = entity.Sequence,
            Kind = entity.Kind,
            AnchorJson = entity.AnchorJson,
            Text = entity.Text,
            ContentHash = entity.ContentHash,
        };
    }

    private static IQueryable<DocumentFragment> ApplyFilters(
        IQueryable<DocumentFragment> query,
        IReadOnlyList<ListDocumentFragmentFilter>? filters)
    {
        if (filters is null || filters.Count == 0)
        {
            return query;
        }

        foreach (var filter in filters)
        {
            if (!HasMeaningfulFilter(filter))
            {
                continue;
            }

            var queryBeforeFilter = query;
            var filterOperator = NormalizeOperator(filter.Operator);
            var normalizedFilterValue = NormalizeSearchValue(filter.Value);
            switch (NormalizeField(filter.Field))
            {
            case "kind":
            {
                var normalizedFilterValues = filter.Values
                    .Select(NormalizeSearchValue)
                    .Where(value => value.Length > 0)
                    .Distinct(StringComparer.Ordinal)
                    .ToList();
                if (normalizedFilterValues.Count == 0)
                {
                    break;
                }
                query = query.Where(item => normalizedFilterValues.Contains(item.KindSearch));
                break;
            }
            case "anchorjson":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.AnchorJsonSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.AnchorJsonSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.AnchorJsonSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "text":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.TextSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.TextSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.TextSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "contenthash":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.ContentHashSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.ContentHashSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.ContentHashSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "id":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.Id == parsedGuid);
                }
                break;
            }
            case "documentrevisionid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.DocumentRevisionId == parsedGuid);
                }
                break;
            }
            default:
                break;
            }

            if (ReferenceEquals(query, queryBeforeFilter))
            {
                return query.Where(item => false);
            }
        }

        return query;
    }

    private static IOrderedQueryable<DocumentFragment> ApplySort(
        IQueryable<DocumentFragment> query,
        IReadOnlyList<ListDocumentFragmentSort>? sortItems)
    {
        IOrderedQueryable<DocumentFragment>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListDocumentFragmentSort>())
        {
            if (string.IsNullOrWhiteSpace(sort.Field))
            {
                continue;
            }

            var orderedBeforeSort = ordered;
            var descending = string.Equals(sort.Direction, "desc", StringComparison.OrdinalIgnoreCase);
            switch (NormalizeField(sort.Field))
            {
            case "id":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Id) : query.OrderBy(item => item.Id))
                    : (descending ? ordered.ThenByDescending(item => item.Id) : ordered.ThenBy(item => item.Id));
                break;
            case "documentrevisionid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.DocumentRevisionId) : query.OrderBy(item => item.DocumentRevisionId))
                    : (descending ? ordered.ThenByDescending(item => item.DocumentRevisionId) : ordered.ThenBy(item => item.DocumentRevisionId));
                break;
            case "sequence":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Sequence) : query.OrderBy(item => item.Sequence))
                    : (descending ? ordered.ThenByDescending(item => item.Sequence) : ordered.ThenBy(item => item.Sequence));
                break;
            case "kind":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Kind) : query.OrderBy(item => item.Kind))
                    : (descending ? ordered.ThenByDescending(item => item.Kind) : ordered.ThenBy(item => item.Kind));
                break;
            case "anchorjson":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.AnchorJson) : query.OrderBy(item => item.AnchorJson))
                    : (descending ? ordered.ThenByDescending(item => item.AnchorJson) : ordered.ThenBy(item => item.AnchorJson));
                break;
            case "text":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Text) : query.OrderBy(item => item.Text))
                    : (descending ? ordered.ThenByDescending(item => item.Text) : ordered.ThenBy(item => item.Text));
                break;
            case "contenthash":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.ContentHash) : query.OrderBy(item => item.ContentHash))
                    : (descending ? ordered.ThenByDescending(item => item.ContentHash) : ordered.ThenBy(item => item.ContentHash));
                break;
            default:
                break;
            }

            if (ReferenceEquals(ordered, orderedBeforeSort))
            {
                return query.Where(item => false).OrderBy(item => 0);
            }
        }

        return ordered ?? query.OrderBy(item => item.Id);
    }

    private static int NormalizePage(int value)
    {
        return value < 1 ? 1 : value;
    }

    private static int NormalizePageSize(int value)
    {
        return Math.Clamp(value, 1, MaxPageSize);
    }

    private static bool HasMeaningfulFilter(ListDocumentFragmentFilter filter)
    {
        return !string.IsNullOrWhiteSpace(filter.Value)
            || filter.Values?.Any(value => !string.IsNullOrWhiteSpace(value)) == true;
    }

    private static string NormalizeField(string? value)
    {
        return value?.Trim().Replace("_", string.Empty, StringComparison.Ordinal).ToLowerInvariant()
            ?? string.Empty;
    }

    private static string NormalizeOperator(string? value)
    {
        var normalized = value?.Trim().Replace("_", string.Empty, StringComparison.Ordinal).ToLowerInvariant();
        return normalized switch
        {
            "equals" => "equals",
            "in" => "in",
            "startswith" => "startsWith",
            _ => "contains",
        };
    }

    private static string NormalizeSearchValue(string? value)
    {
        return value?.Trim().ToUpperInvariant() ?? string.Empty;
    }


}
