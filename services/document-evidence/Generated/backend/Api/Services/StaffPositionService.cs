#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class StaffPositionService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public StaffPositionService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListStaffPositionResult> ListAsync(
        ListStaffPositionRequest request,
        Func<IQueryable<StaffPosition>, IQueryable<StaffPosition>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<StaffPosition> query = _db.StaffPositions.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListStaffPositionResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<StaffPosition?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<StaffPosition> query = _db.StaffPositions;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionLookupDto>> LookupAsync(
        LookupStaffPositionRequest request,
        Func<IQueryable<StaffPosition>, IQueryable<StaffPosition>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositions.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.Name.ToUpper().Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.Name);

        return await query
            .Take(take)
            .Select(item => new StaffPositionLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Name,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionSuggestionDto>> SuggestAsync(
        string field,
        SuggestStaffPositionRequest request,
        Func<IQueryable<StaffPosition>, IQueryable<StaffPosition>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "code":
                return await query
                    .Where(item => item.Code != null)
                    .Where(item => normalizedQuery.Length == 0 || item.Code.ToUpper().Contains(normalizedQuery))
                    .Select(item => item.Code!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StaffPositionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "name":
                return await query
                    .Where(item => item.Name != null)
                    .Where(item => normalizedQuery.Length == 0 || item.Name.ToUpper().Contains(normalizedQuery))
                    .Select(item => item.Name!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StaffPositionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "description":
                return await query
                    .Where(item => item.Description != null)
                    .Where(item => normalizedQuery.Length == 0 || (item.Description ?? string.Empty).ToUpper().Contains(normalizedQuery))
                    .Select(item => item.Description!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StaffPositionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<StaffPositionSuggestionDto>();
    }

    public async Task<IReadOnlyList<StaffPositionOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<StaffPosition>, IQueryable<StaffPosition>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.StaffPositions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<StaffPositionOptionDto>();
    }

    public async Task<StaffPosition> CreateAsync(
        CreateStaffPositionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new StaffPosition
        {
            Id = Guid.NewGuid(),
            Code = request.Code,
            Name = request.Name,
            Description = request.Description,
            ParentPositionId = request.ParentPositionId,
            IsActive = request.IsActive,
        };

        _db.StaffPositions.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<StaffPosition> UpdateAsync(
        StaffPosition entity,
        UpdateStaffPositionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.Code = request.Code;
        entity.Name = request.Name;
        entity.Description = request.Description;
        entity.ParentPositionId = request.ParentPositionId;
        entity.IsActive = request.IsActive;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        StaffPosition entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        _db.StaffPositions.Remove(entity);

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        StaffPosition entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public StaffPositionDto ToDto(StaffPosition entity)
    {
        return new StaffPositionDto
        {
            Id = entity.Id,
            Code = entity.Code,
            Name = entity.Name,
            Description = entity.Description,
            ParentPositionId = entity.ParentPositionId,
            IsActive = entity.IsActive,
        };
    }

    private static IQueryable<StaffPosition> ApplyFilters(
        IQueryable<StaffPosition> query,
        IReadOnlyList<ListStaffPositionFilter>? filters)
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
            case "code":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.Code.ToUpper() == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.Code.ToUpper().StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.Code.ToUpper().Contains(normalizedFilterValue)),
                };
                break;
            case "name":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.Name.ToUpper() == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.Name.ToUpper().StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.Name.ToUpper().Contains(normalizedFilterValue)),
                };
                break;
            case "description":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => (item.Description ?? string.Empty).ToUpper() == normalizedFilterValue),
                    "startsWith" => query.Where(item => (item.Description ?? string.Empty).ToUpper().StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => (item.Description ?? string.Empty).ToUpper().Contains(normalizedFilterValue)),
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
            case "parentpositionid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.ParentPositionId == parsedGuid);
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

    private static IOrderedQueryable<StaffPosition> ApplySort(
        IQueryable<StaffPosition> query,
        IReadOnlyList<ListStaffPositionSort>? sortItems)
    {
        IOrderedQueryable<StaffPosition>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListStaffPositionSort>())
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
            case "code":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Code) : query.OrderBy(item => item.Code))
                    : (descending ? ordered.ThenByDescending(item => item.Code) : ordered.ThenBy(item => item.Code));
                break;
            case "name":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Name) : query.OrderBy(item => item.Name))
                    : (descending ? ordered.ThenByDescending(item => item.Name) : ordered.ThenBy(item => item.Name));
                break;
            case "description":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Description) : query.OrderBy(item => item.Description))
                    : (descending ? ordered.ThenByDescending(item => item.Description) : ordered.ThenBy(item => item.Description));
                break;
            case "parentpositionid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.ParentPositionId) : query.OrderBy(item => item.ParentPositionId))
                    : (descending ? ordered.ThenByDescending(item => item.ParentPositionId) : ordered.ThenBy(item => item.ParentPositionId));
                break;
            case "isactive":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.IsActive) : query.OrderBy(item => item.IsActive))
                    : (descending ? ordered.ThenByDescending(item => item.IsActive) : ordered.ThenBy(item => item.IsActive));
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

    private static bool HasMeaningfulFilter(ListStaffPositionFilter filter)
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
