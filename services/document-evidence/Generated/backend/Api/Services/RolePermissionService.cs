#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class RolePermissionService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public RolePermissionService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListRolePermissionResult> ListAsync(
        ListRolePermissionRequest request,
        Func<IQueryable<RolePermission>, IQueryable<RolePermission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<RolePermission> query = _db.RolePermissions.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListRolePermissionResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<RolePermission?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<RolePermission> query = _db.RolePermissions;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<RolePermissionLookupDto>> LookupAsync(
        LookupRolePermissionRequest request,
        Func<IQueryable<RolePermission>, IQueryable<RolePermission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.RolePermissions.AsNoTracking();
        query = authorizeQuery(query);

        query = query.OrderBy(item => item.Id);

        return await query
            .Take(take)
            .Select(item => new RolePermissionLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Id.ToString(),
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<RolePermissionSuggestionDto>> SuggestAsync(
        string field,
        SuggestRolePermissionRequest request,
        Func<IQueryable<RolePermission>, IQueryable<RolePermission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.RolePermissions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<RolePermissionSuggestionDto>();
    }

    public async Task<IReadOnlyList<RolePermissionOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<RolePermission>, IQueryable<RolePermission>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.RolePermissions.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<RolePermissionOptionDto>();
    }

    public async Task<RolePermission> CreateAsync(
        CreateRolePermissionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new RolePermission
        {
            Id = Guid.NewGuid(),
            RoleId = request.RoleId,
            PermissionId = request.PermissionId,
        };

        _db.RolePermissions.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<RolePermission> UpdateAsync(
        RolePermission entity,
        UpdateRolePermissionRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.RoleId = request.RoleId;
        entity.PermissionId = request.PermissionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        RolePermission entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        _db.RolePermissions.Remove(entity);

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        RolePermission entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public RolePermissionDto ToDto(RolePermission entity)
    {
        return new RolePermissionDto
        {
            Id = entity.Id,
            RoleId = entity.RoleId,
            PermissionId = entity.PermissionId,
        };
    }

    private static IQueryable<RolePermission> ApplyFilters(
        IQueryable<RolePermission> query,
        IReadOnlyList<ListRolePermissionFilter>? filters)
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
            case "roleid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.RoleId == parsedGuid);
                }
                break;
            }
            case "permissionid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.PermissionId == parsedGuid);
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

    private static IOrderedQueryable<RolePermission> ApplySort(
        IQueryable<RolePermission> query,
        IReadOnlyList<ListRolePermissionSort>? sortItems)
    {
        IOrderedQueryable<RolePermission>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListRolePermissionSort>())
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
            case "roleid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.RoleId) : query.OrderBy(item => item.RoleId))
                    : (descending ? ordered.ThenByDescending(item => item.RoleId) : ordered.ThenBy(item => item.RoleId));
                break;
            case "permissionid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.PermissionId) : query.OrderBy(item => item.PermissionId))
                    : (descending ? ordered.ThenByDescending(item => item.PermissionId) : ordered.ThenBy(item => item.PermissionId));
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

    private static bool HasMeaningfulFilter(ListRolePermissionFilter filter)
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
