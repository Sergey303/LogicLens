#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class StoredObjectService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public StoredObjectService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListStoredObjectResult> ListAsync(
        ListStoredObjectRequest request,
        Func<IQueryable<StoredObject>, IQueryable<StoredObject>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<StoredObject> query = _db.StoredObjects.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListStoredObjectResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<StoredObject?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<StoredObject> query = _db.StoredObjects;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<StoredObjectLookupDto>> LookupAsync(
        LookupStoredObjectRequest request,
        Func<IQueryable<StoredObject>, IQueryable<StoredObject>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StoredObjects.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.Sha256Search.Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.Sha256);

        return await query
            .Take(take)
            .Select(item => new StoredObjectLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Sha256,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<StoredObjectSuggestionDto>> SuggestAsync(
        string field,
        SuggestStoredObjectRequest request,
        Func<IQueryable<StoredObject>, IQueryable<StoredObject>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StoredObjects.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "sha256":
                return await query
                    .Where(item => item.Sha256 != null)
                    .Where(item => normalizedQuery.Length == 0 || item.Sha256Search.Contains(normalizedQuery))
                    .Select(item => item.Sha256!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StoredObjectSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "storagekey":
                return await query
                    .Where(item => item.StorageKey != null)
                    .Where(item => normalizedQuery.Length == 0 || item.StorageKeySearch.Contains(normalizedQuery))
                    .Select(item => item.StorageKey!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StoredObjectSuggestionDto
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
                    .Select(value => new StoredObjectSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<StoredObjectSuggestionDto>();
    }

    public async Task<IReadOnlyList<StoredObjectOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<StoredObject>, IQueryable<StoredObject>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.StoredObjects.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<StoredObjectOptionDto>();
    }

    public async Task<StoredObject> CreateAsync(
        CreateStoredObjectRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new StoredObject
        {
            Id = Guid.NewGuid(),
            Sha256 = request.Sha256,
            StorageKey = request.StorageKey,
            SizeBytes = request.SizeBytes,
            MediaType = request.MediaType,
            CreationTime = DateTime.UtcNow,
            CreatorId = currentUserId,
            CreatorPositionId = currentAuditPositionId,
            IsDeleted = false,
            Sha256Search = NormalizeSearchValue(request.Sha256),
            StorageKeySearch = NormalizeSearchValue(request.StorageKey),
            MediaTypeSearch = NormalizeSearchValue(request.MediaType),
        };

        _db.StoredObjects.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<StoredObject> UpdateAsync(
        StoredObject entity,
        UpdateStoredObjectRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.Sha256 = request.Sha256;
        entity.StorageKey = request.StorageKey;
        entity.SizeBytes = request.SizeBytes;
        entity.MediaType = request.MediaType;
        entity.Sha256Search = NormalizeSearchValue(request.Sha256);
        entity.StorageKeySearch = NormalizeSearchValue(request.StorageKey);
        entity.MediaTypeSearch = NormalizeSearchValue(request.MediaType);
        entity.LastModificationTime = DateTime.UtcNow;
        entity.LastModifierId = currentUserId;
        entity.LastModifierPositionId = currentAuditPositionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        StoredObject entity,
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
        StoredObject entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public StoredObjectDto ToDto(StoredObject entity)
    {
        return new StoredObjectDto
        {
            Id = entity.Id,
            Sha256 = entity.Sha256,
            StorageKey = entity.StorageKey,
            SizeBytes = entity.SizeBytes,
            MediaType = entity.MediaType,
        };
    }

    private static IQueryable<StoredObject> ApplyFilters(
        IQueryable<StoredObject> query,
        IReadOnlyList<ListStoredObjectFilter>? filters)
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
            case "sha256":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.Sha256Search == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.Sha256Search.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.Sha256Search.Contains(normalizedFilterValue)),
                };
                break;
            case "storagekey":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.StorageKeySearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.StorageKeySearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.StorageKeySearch.Contains(normalizedFilterValue)),
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
            case "id":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.Id == parsedGuid);
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

    private static IOrderedQueryable<StoredObject> ApplySort(
        IQueryable<StoredObject> query,
        IReadOnlyList<ListStoredObjectSort>? sortItems)
    {
        IOrderedQueryable<StoredObject>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListStoredObjectSort>())
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
            case "sha256":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Sha256) : query.OrderBy(item => item.Sha256))
                    : (descending ? ordered.ThenByDescending(item => item.Sha256) : ordered.ThenBy(item => item.Sha256));
                break;
            case "storagekey":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.StorageKey) : query.OrderBy(item => item.StorageKey))
                    : (descending ? ordered.ThenByDescending(item => item.StorageKey) : ordered.ThenBy(item => item.StorageKey));
                break;
            case "sizebytes":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.SizeBytes) : query.OrderBy(item => item.SizeBytes))
                    : (descending ? ordered.ThenByDescending(item => item.SizeBytes) : ordered.ThenBy(item => item.SizeBytes));
                break;
            case "mediatype":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.MediaType) : query.OrderBy(item => item.MediaType))
                    : (descending ? ordered.ThenByDescending(item => item.MediaType) : ordered.ThenBy(item => item.MediaType));
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

    private static bool HasMeaningfulFilter(ListStoredObjectFilter filter)
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
