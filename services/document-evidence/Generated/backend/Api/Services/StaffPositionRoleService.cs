#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class StaffPositionRoleService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public StaffPositionRoleService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListStaffPositionRoleResult> ListAsync(
        ListStaffPositionRoleRequest request,
        Func<IQueryable<StaffPositionRole>, IQueryable<StaffPositionRole>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<StaffPositionRole> query = _db.StaffPositionRoles.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListStaffPositionRoleResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<StaffPositionRole?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<StaffPositionRole> query = _db.StaffPositionRoles;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionRoleLookupDto>> LookupAsync(
        LookupStaffPositionRoleRequest request,
        Func<IQueryable<StaffPositionRole>, IQueryable<StaffPositionRole>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositionRoles.AsNoTracking();
        query = authorizeQuery(query);

        query = query.OrderBy(item => item.Id);

        return await query
            .Take(take)
            .Select(item => new StaffPositionRoleLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Id.ToString(),
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionRoleSuggestionDto>> SuggestAsync(
        string field,
        SuggestStaffPositionRoleRequest request,
        Func<IQueryable<StaffPositionRole>, IQueryable<StaffPositionRole>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositionRoles.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<StaffPositionRoleSuggestionDto>();
    }

    public async Task<IReadOnlyList<StaffPositionRoleOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<StaffPositionRole>, IQueryable<StaffPositionRole>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.StaffPositionRoles.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<StaffPositionRoleOptionDto>();
    }

    public async Task<StaffPositionRole> CreateAsync(
        CreateStaffPositionRoleRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new StaffPositionRole
        {
            Id = Guid.NewGuid(),
            StaffPositionId = request.StaffPositionId,
            RoleId = request.RoleId,
        };

        _db.StaffPositionRoles.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<StaffPositionRole> UpdateAsync(
        StaffPositionRole entity,
        UpdateStaffPositionRoleRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.StaffPositionId = request.StaffPositionId;
        entity.RoleId = request.RoleId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        StaffPositionRole entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        _db.StaffPositionRoles.Remove(entity);

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        StaffPositionRole entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public StaffPositionRoleDto ToDto(StaffPositionRole entity)
    {
        return new StaffPositionRoleDto
        {
            Id = entity.Id,
            StaffPositionId = entity.StaffPositionId,
            RoleId = entity.RoleId,
        };
    }

    private static IQueryable<StaffPositionRole> ApplyFilters(
        IQueryable<StaffPositionRole> query,
        IReadOnlyList<ListStaffPositionRoleFilter>? filters)
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
            case "id":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.Id == parsedGuid);
                }
                break;
            }
            case "staffpositionid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.StaffPositionId == parsedGuid);
                }
                break;
            }
            case "roleid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.RoleId == parsedGuid);
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

    private static IOrderedQueryable<StaffPositionRole> ApplySort(
        IQueryable<StaffPositionRole> query,
        IReadOnlyList<ListStaffPositionRoleSort>? sortItems)
    {
        IOrderedQueryable<StaffPositionRole>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListStaffPositionRoleSort>())
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
            case "staffpositionid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.StaffPositionId) : query.OrderBy(item => item.StaffPositionId))
                    : (descending ? ordered.ThenByDescending(item => item.StaffPositionId) : ordered.ThenBy(item => item.StaffPositionId));
                break;
            case "roleid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.RoleId) : query.OrderBy(item => item.RoleId))
                    : (descending ? ordered.ThenByDescending(item => item.RoleId) : ordered.ThenBy(item => item.RoleId));
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

    private static bool HasMeaningfulFilter(ListStaffPositionRoleFilter filter)
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
