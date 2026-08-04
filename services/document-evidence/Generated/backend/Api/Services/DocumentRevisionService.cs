#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class DocumentRevisionService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public DocumentRevisionService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListDocumentRevisionResult> ListAsync(
        ListDocumentRevisionRequest request,
        Func<IQueryable<DocumentRevision>, IQueryable<DocumentRevision>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<DocumentRevision> query = _db.DocumentRevisions.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListDocumentRevisionResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<DocumentRevision?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<DocumentRevision> query = _db.DocumentRevisions;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentRevisionLookupDto>> LookupAsync(
        LookupDocumentRevisionRequest request,
        Func<IQueryable<DocumentRevision>, IQueryable<DocumentRevision>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.DocumentRevisions.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.StateSearch.Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.State);

        return await query
            .Take(take)
            .Select(item => new DocumentRevisionLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.State,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<DocumentRevisionSuggestionDto>> SuggestAsync(
        string field,
        SuggestDocumentRevisionRequest request,
        Func<IQueryable<DocumentRevision>, IQueryable<DocumentRevision>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.DocumentRevisions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "state":
                return await query
                    .Where(item => item.State != null)
                    .Where(item => normalizedQuery.Length == 0 || item.StateSearch.Contains(normalizedQuery))
                    .Select(item => item.State!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentRevisionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "adapter":
                return await query
                    .Where(item => item.Adapter != null)
                    .Where(item => normalizedQuery.Length == 0 || item.AdapterSearch.Contains(normalizedQuery))
                    .Select(item => item.Adapter!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentRevisionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "adapterversion":
                return await query
                    .Where(item => item.AdapterVersion != null)
                    .Where(item => normalizedQuery.Length == 0 || item.AdapterVersionSearch.Contains(normalizedQuery))
                    .Select(item => item.AdapterVersion!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentRevisionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "manifesthash":
                return await query
                    .Where(item => item.ManifestHash != null)
                    .Where(item => normalizedQuery.Length == 0 || item.ManifestHashSearch.Contains(normalizedQuery))
                    .Select(item => item.ManifestHash!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new DocumentRevisionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentRevisionSuggestionDto>();
    }

    public async Task<IReadOnlyList<DocumentRevisionOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<DocumentRevision>, IQueryable<DocumentRevision>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.DocumentRevisions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "state":
                return await query
                    .Where(item => item.State != null)
                    .Select(item => item.State!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Select(value => new DocumentRevisionOptionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<DocumentRevisionOptionDto>();
    }

    public async Task<DocumentRevision> CreateAsync(
        CreateDocumentRevisionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new DocumentRevision
        {
            Id = Guid.NewGuid(),
            DocumentId = request.DocumentId,
            StoredObjectId = request.StoredObjectId,
            RevisionNumber = request.RevisionNumber,
            State = request.State,
            Adapter = request.Adapter,
            AdapterVersion = request.AdapterVersion,
            ManifestHash = request.ManifestHash,
            CreationTime = DateTime.UtcNow,
            CreatorId = currentUserId,
            CreatorPositionId = currentAuditPositionId,
            IsDeleted = false,
            StateSearch = NormalizeSearchValue(request.State),
            AdapterSearch = NormalizeSearchValue(request.Adapter),
            AdapterVersionSearch = NormalizeSearchValue(request.AdapterVersion),
            ManifestHashSearch = NormalizeSearchValue(request.ManifestHash),
        };

        _db.DocumentRevisions.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<DocumentRevision> UpdateAsync(
        DocumentRevision entity,
        UpdateDocumentRevisionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.DocumentId = request.DocumentId;
        entity.StoredObjectId = request.StoredObjectId;
        entity.RevisionNumber = request.RevisionNumber;
        entity.State = request.State;
        entity.Adapter = request.Adapter;
        entity.AdapterVersion = request.AdapterVersion;
        entity.ManifestHash = request.ManifestHash;
        entity.StateSearch = NormalizeSearchValue(request.State);
        entity.AdapterSearch = NormalizeSearchValue(request.Adapter);
        entity.AdapterVersionSearch = NormalizeSearchValue(request.AdapterVersion);
        entity.ManifestHashSearch = NormalizeSearchValue(request.ManifestHash);
        entity.LastModificationTime = DateTime.UtcNow;
        entity.LastModifierId = currentUserId;
        entity.LastModifierPositionId = currentAuditPositionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        DocumentRevision entity,
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
        DocumentRevision entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public DocumentRevisionDto ToDto(DocumentRevision entity)
    {
        return new DocumentRevisionDto
        {
            Id = entity.Id,
            DocumentId = entity.DocumentId,
            StoredObjectId = entity.StoredObjectId,
            RevisionNumber = entity.RevisionNumber,
            State = entity.State,
            Adapter = entity.Adapter,
            AdapterVersion = entity.AdapterVersion,
            ManifestHash = entity.ManifestHash,
        };
    }

    private static IQueryable<DocumentRevision> ApplyFilters(
        IQueryable<DocumentRevision> query,
        IReadOnlyList<ListDocumentRevisionFilter>? filters)
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
            case "adapter":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.AdapterSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.AdapterSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.AdapterSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "adapterversion":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.AdapterVersionSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.AdapterVersionSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.AdapterVersionSearch.Contains(normalizedFilterValue)),
                };
                break;
            case "manifesthash":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.ManifestHashSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.ManifestHashSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.ManifestHashSearch.Contains(normalizedFilterValue)),
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
            case "documentid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.DocumentId == parsedGuid);
                }
                break;
            }
            case "storedobjectid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.StoredObjectId == parsedGuid);
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

    private static IOrderedQueryable<DocumentRevision> ApplySort(
        IQueryable<DocumentRevision> query,
        IReadOnlyList<ListDocumentRevisionSort>? sortItems)
    {
        IOrderedQueryable<DocumentRevision>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListDocumentRevisionSort>())
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
            case "documentid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.DocumentId) : query.OrderBy(item => item.DocumentId))
                    : (descending ? ordered.ThenByDescending(item => item.DocumentId) : ordered.ThenBy(item => item.DocumentId));
                break;
            case "storedobjectid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.StoredObjectId) : query.OrderBy(item => item.StoredObjectId))
                    : (descending ? ordered.ThenByDescending(item => item.StoredObjectId) : ordered.ThenBy(item => item.StoredObjectId));
                break;
            case "revisionnumber":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.RevisionNumber) : query.OrderBy(item => item.RevisionNumber))
                    : (descending ? ordered.ThenByDescending(item => item.RevisionNumber) : ordered.ThenBy(item => item.RevisionNumber));
                break;
            case "state":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.State) : query.OrderBy(item => item.State))
                    : (descending ? ordered.ThenByDescending(item => item.State) : ordered.ThenBy(item => item.State));
                break;
            case "adapter":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Adapter) : query.OrderBy(item => item.Adapter))
                    : (descending ? ordered.ThenByDescending(item => item.Adapter) : ordered.ThenBy(item => item.Adapter));
                break;
            case "adapterversion":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.AdapterVersion) : query.OrderBy(item => item.AdapterVersion))
                    : (descending ? ordered.ThenByDescending(item => item.AdapterVersion) : ordered.ThenBy(item => item.AdapterVersion));
                break;
            case "manifesthash":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.ManifestHash) : query.OrderBy(item => item.ManifestHash))
                    : (descending ? ordered.ThenByDescending(item => item.ManifestHash) : ordered.ThenBy(item => item.ManifestHash));
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

    private static bool HasMeaningfulFilter(ListDocumentRevisionFilter filter)
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
