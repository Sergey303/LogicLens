#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class DocumentService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public DocumentService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListDocumentResult> ListAsync(
        ListDocumentRequest request,
        Func<IQueryable<Document>, IQueryable<Document>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<Document> query = _db.Documents.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListDocumentResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<Document?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<Document> query = _db.Documents;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentLookupDto>> LookupAsync(
        LookupDocumentRequest request,
        Func<IQueryable<Document>, IQueryable<Document>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.Documents.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.DisplayNameSearch.Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.DisplayName);

        return await query
            .Take(take)
            .Select(item => new DocumentLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.DisplayName,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentSuggestionDto>> SuggestAsync(
        string field,
        SuggestDocumentRequest request,
        Func<IQueryable<Document>, IQueryable<Document>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.Documents.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "displayname":
                return await query
                    .Where(item => item.DisplayName != null)
                    .Where(item => normalizedQuery.Length == 0 || item.DisplayNameSearch.Contains(normalizedQuery))
                    .Select(item => item.DisplayName!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "mediatype":
                return await query
                    .Where(item => item.MediaType != null)
                    .Where(item => normalizedQuery.Length == 0 || item.MediaTypeSearch.Contains(normalizedQuery))
                    .Select(item => item.MediaType!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "sourcekind":
                return await query
                    .Where(item => item.SourceKind != null)
                    .Where(item => normalizedQuery.Length == 0 || item.SourceKindSearch.Contains(normalizedQuery))
                    .Select(item => item.SourceKind!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "state":
                return await query
                    .Where(item => item.State != null)
                    .Where(item => normalizedQuery.Length == 0 || item.StateSearch.Contains(normalizedQuery))
                    .Select(item => item.State!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentSuggestionDto>();
    }

    public async Task<IReadOnlyList<DocumentOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<Document>, IQueryable<Document>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.Documents.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "state":
                return await query
                    .Where(item => item.State != null)
                    .Select(item => item.State!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Select(value => new DocumentOptionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentOptionDto>();
    }

    public async Task<Document> CreateAsync(
        CreateDocumentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new Document
        {
            Id = Guid.NewGuid(),
            WorkspaceId = request.WorkspaceId,
            DisplayName = request.DisplayName,
            MediaType = request.MediaType,
            SourceKind = request.SourceKind,
            State = request.State,
            CurrentRevisionNumber = request.CurrentRevisionNumber,
            IsRevoked = request.IsRevoked,
            CreationTime = DateTime.UtcNow,
            CreatorId = currentUserId,
            CreatorPositionId = currentAuditPositionId,
            IsDeleted = false,
            DisplayNameSearch = NormalizeSearchValue(request.DisplayName),
            MediaTypeSearch = NormalizeSearchValue(request.MediaType),
            SourceKindSearch = NormalizeSearchValue(request.SourceKind),
            StateSearch = NormalizeSearchValue(request.State),
        };

        _db.Documents.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<Document> UpdateAsync(
        Document entity,
        UpdateDocumentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.WorkspaceId = request.WorkspaceId;
        entity.DisplayName = request.DisplayName;
        entity.MediaType = request.MediaType;
        entity.SourceKind = request.SourceKind;
        entity.State = request.State;
        entity.CurrentRevisionNumber = request.CurrentRevisionNumber;
        entity.IsRevoked = request.IsRevoked;
        entity.DisplayNameSearch = NormalizeSearchValue(request.DisplayName);
        entity.MediaTypeSearch = NormalizeSearchValue(request.MediaType);
        entity.SourceKindSearch = NormalizeSearchValue(request.SourceKind);
        entity.StateSearch = NormalizeSearchValue(request.State);
        entity.LastModificationTime = DateTime.UtcNow;
        entity.LastModifierId = currentUserId;
        entity.LastModifierPositionId = currentAuditPositionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        Document entity,
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
        Document entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public DocumentDto ToDto(Document entity)
    {
        return new DocumentDto
        {
            Id = entity.Id,
            WorkspaceId = entity.WorkspaceId,
            DisplayName = entity.DisplayName,
            MediaType = entity.MediaType,
            SourceKind = entity.SourceKind,
            State = entity.State,
            CurrentRevisionNumber = entity.CurrentRevisionNumber,
            IsRevoked = entity.IsRevoked,
        };
    }

    private static IQueryable<Document> ApplyFilters(
        IQueryable<Document> query,
        IReadOnlyList<ListDocumentFilter>? filters)
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
            case "state":
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
                query = query.Where(item => normalizedFilterValues.Contains(item.StateSearch));
                break;
            }
            case "displayname":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.DisplayNameSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.DisplayNameSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.DisplayNameSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "mediatype":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.MediaTypeSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.MediaTypeSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.MediaTypeSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "sourcekind":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.SourceKindSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.SourceKindSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.SourceKindSearch.Contains(normalizedFilterValue)),
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
            case "workspaceid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.WorkspaceId == parsedGuid);
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

    private static IOrderedQueryable<Document> ApplySort(
        IQueryable<Document> query,
        IReadOnlyList<ListDocumentSort>? sortItems)
    {
        IOrderedQueryable<Document>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListDocumentSort>())
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
            case "workspaceid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.WorkspaceId) : query.OrderBy(item => item.WorkspaceId))
                    : (descending ? ordered.ThenByDescending(item => item.WorkspaceId) : ordered.ThenBy(item => item.WorkspaceId));
                break;
            case "displayname":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.DisplayName) : query.OrderBy(item => item.DisplayName))
                    : (descending ? ordered.ThenByDescending(item => item.DisplayName) : ordered.ThenBy(item => item.DisplayName));
                break;
            case "mediatype":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.MediaType) : query.OrderBy(item => item.MediaType))
                    : (descending ? ordered.ThenByDescending(item => item.MediaType) : ordered.ThenBy(item => item.MediaType));
                break;
            case "sourcekind":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.SourceKind) : query.OrderBy(item => item.SourceKind))
                    : (descending ? ordered.ThenByDescending(item => item.SourceKind) : ordered.ThenBy(item => item.SourceKind));
                break;
            case "state":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.State) : query.OrderBy(item => item.State))
                    : (descending ? ordered.ThenByDescending(item => item.State) : ordered.ThenBy(item => item.State));
                break;
            case "currentrevisionnumber":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.CurrentRevisionNumber) : query.OrderBy(item => item.CurrentRevisionNumber))
                    : (descending ? ordered.ThenByDescending(item => item.CurrentRevisionNumber) : ordered.ThenBy(item => item.CurrentRevisionNumber));
                break;
            case "isrevoked":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.IsRevoked) : query.OrderBy(item => item.IsRevoked))
                    : (descending ? ordered.ThenByDescending(item => item.IsRevoked) : ordered.ThenBy(item => item.IsRevoked));
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

    private static bool HasMeaningfulFilter(ListDocumentFilter filter)
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
