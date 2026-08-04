#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class PermissionService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public PermissionService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListPermissionResult> ListAsync(
        ListPermissionRequest request,
        Func<IQueryable<Permission>, IQueryable<Permission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<Permission> query = _db.Permissions.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListPermissionResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<Permission?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<Permission> query = _db.Permissions;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<PermissionLookupDto>> LookupAsync(
        LookupPermissionRequest request,
        Func<IQueryable<Permission>, IQueryable<Permission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.Permissions.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.Name.ToUpper().Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.Name);

        return await query
            .Take(take)
            .Select(item => new PermissionLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Name,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<PermissionSuggestionDto>> SuggestAsync(
        string field,
        SuggestPermissionRequest request,
        Func<IQueryable<Permission>, IQueryable<Permission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.Permissions.AsNoTracking();
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
                    .Select(value => new PermissionSuggestionDto
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
                    .Select(value => new PermissionSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<PermissionSuggestionDto>();
    }

    public async Task<IReadOnlyList<PermissionOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<Permission>, IQueryable<Permission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.Permissions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<PermissionOptionDto>();
    }

    public async Task<Permission> CreateAsync(
        CreatePermissionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new Permission
        {
            Id = Guid.NewGuid(),
            Code = request.Code,
            Name = request.Name,
        };

        _db.Permissions.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<Permission> UpdateAsync(
        Permission entity,
        UpdatePermissionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.Code = request.Code;
        entity.Name = request.Name;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        Permission entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        _db.Permissions.Remove(entity);

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        Permission entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public PermissionDto ToDto(Permission entity)
    {
        return new PermissionDto
        {
            Id = entity.Id,
            Code = entity.Code,
            Name = entity.Name,
        };
    }

    private static IQueryable<Permission> ApplyFilters(
        IQueryable<Permission> query,
        IReadOnlyList<ListPermissionFilter>? filters)
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

    private static IOrderedQueryable<Permission> ApplySort(
        IQueryable<Permission> query,
        IReadOnlyList<ListPermissionSort>? sortItems)
    {
        IOrderedQueryable<Permission>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListPermissionSort>())
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

    private static bool HasMeaningfulFilter(ListPermissionFilter filter)
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
