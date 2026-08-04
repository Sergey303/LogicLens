#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class StaffPositionAssignmentService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public StaffPositionAssignmentService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListStaffPositionAssignmentResult> ListAsync(
        ListStaffPositionAssignmentRequest request,
        Func<IQueryable<StaffPositionAssignment>, IQueryable<StaffPositionAssignment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<StaffPositionAssignment> query = _db.StaffPositionAssignments.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListStaffPositionAssignmentResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<StaffPositionAssignment?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<StaffPositionAssignment> query = _db.StaffPositionAssignments;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionAssignmentLookupDto>> LookupAsync(
        LookupStaffPositionAssignmentRequest request,
        Func<IQueryable<StaffPositionAssignment>, IQueryable<StaffPositionAssignment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositionAssignments.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.AssignmentKind.ToUpper().Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.AssignmentKind);

        return await query
            .Take(take)
            .Select(item => new StaffPositionAssignmentLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.AssignmentKind,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<StaffPositionAssignmentSuggestionDto>> SuggestAsync(
        string field,
        SuggestStaffPositionAssignmentRequest request,
        Func<IQueryable<StaffPositionAssignment>, IQueryable<StaffPositionAssignment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.StaffPositionAssignments.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "assignmentkind":
                return await query
                    .Where(item => item.AssignmentKind != null)
                    .Where(item => normalizedQuery.Length == 0 || item.AssignmentKind.ToUpper().Contains(normalizedQuery))
                    .Select(item => item.AssignmentKind!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StaffPositionAssignmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "reason":
                return await query
                    .Where(item => item.Reason != null)
                    .Where(item => normalizedQuery.Length == 0 || (item.Reason ?? string.Empty).ToUpper().Contains(normalizedQuery))
                    .Select(item => item.Reason!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new StaffPositionAssignmentSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<StaffPositionAssignmentSuggestionDto>();
    }

    public async Task<IReadOnlyList<StaffPositionAssignmentOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<StaffPositionAssignment>, IQueryable<StaffPositionAssignment>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.StaffPositionAssignments.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            default:
                break;
        }

        return Array.Empty<StaffPositionAssignmentOptionDto>();
    }

    public async Task<StaffPositionAssignment> CreateAsync(
        CreateStaffPositionAssignmentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new StaffPositionAssignment
        {
            Id = Guid.NewGuid(),
            StaffPositionId = request.StaffPositionId,
            UserId = request.UserId,
            AssignmentKind = request.AssignmentKind,
            StartsAt = request.StartsAt,
            EndsAt = request.EndsAt,
            StartsAtUtc = request.StartsAtUtc,
            EndsAtUtc = request.EndsAtUtc,
            IsActive = request.IsActive,
            Reason = request.Reason,
        };

        _db.StaffPositionAssignments.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<StaffPositionAssignment> UpdateAsync(
        StaffPositionAssignment entity,
        UpdateStaffPositionAssignmentRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.StaffPositionId = request.StaffPositionId;
        entity.UserId = request.UserId;
        entity.AssignmentKind = request.AssignmentKind;
        entity.StartsAt = request.StartsAt;
        entity.EndsAt = request.EndsAt;
        entity.StartsAtUtc = request.StartsAtUtc;
        entity.EndsAtUtc = request.EndsAtUtc;
        entity.IsActive = request.IsActive;
        entity.Reason = request.Reason;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        StaffPositionAssignment entity,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        _db.StaffPositionAssignments.Remove(entity);

        await _db.SaveChangesAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetMutationWarningsAsync(
        StaffPositionAssignment entity,
        CancellationToken cancellationToken)
    {
        if (!entity.IsActive || !IsPrimaryAssignment(entity.AssignmentKind))
        {
            return Array.Empty<string>();
        }

        var warnings = new List<string>();
        var assignmentEndsAt = AssignmentIntervalEnd(entity.EndsAt);

        var userPrimaryConflict = await _db.StaffPositionAssignments
            .AsNoTracking()
            .AnyAsync(item =>
                item.Id != entity.Id
                && item.UserId == entity.UserId
                && item.IsActive
                && item.AssignmentKind.ToUpper() == "PRIMARY"
                && item.StartsAt < assignmentEndsAt
                && (!item.EndsAt.HasValue || entity.StartsAt < item.EndsAt.Value),
                cancellationToken);
        if (userPrimaryConflict)
        {
            warnings.Add("staff-position-assignment.user-has-another-active-primary");
        }

        var positionPrimaryConflict = await _db.StaffPositionAssignments
            .AsNoTracking()
            .AnyAsync(item =>
                item.Id != entity.Id
                && item.StaffPositionId == entity.StaffPositionId
                && item.IsActive
                && item.AssignmentKind.ToUpper() == "PRIMARY"
                && item.StartsAt < assignmentEndsAt
                && (!item.EndsAt.HasValue || entity.StartsAt < item.EndsAt.Value),
                cancellationToken);
        if (positionPrimaryConflict)
        {
            warnings.Add("staff-position-assignment.position-has-another-active-primary");
        }

        return warnings;
    }

    public StaffPositionAssignmentDto ToDto(StaffPositionAssignment entity)
    {
        return new StaffPositionAssignmentDto
        {
            Id = entity.Id,
            StaffPositionId = entity.StaffPositionId,
            UserId = entity.UserId,
            AssignmentKind = entity.AssignmentKind,
            StartsAt = entity.StartsAt,
            EndsAt = entity.EndsAt,
            StartsAtUtc = entity.StartsAtUtc,
            EndsAtUtc = entity.EndsAtUtc,
            IsActive = entity.IsActive,
            Reason = entity.Reason,
        };
    }

    private static IQueryable<StaffPositionAssignment> ApplyFilters(
        IQueryable<StaffPositionAssignment> query,
        IReadOnlyList<ListStaffPositionAssignmentFilter>? filters)
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
            case "assignmentkind":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.AssignmentKind.ToUpper() == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.AssignmentKind.ToUpper().StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.AssignmentKind.ToUpper().Contains(normalizedFilterValue)),
                };
                break;
            case "reason":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => (item.Reason ?? string.Empty).ToUpper() == normalizedFilterValue),
                    "startsWith" => query.Where(item => (item.Reason ?? string.Empty).ToUpper().StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => (item.Reason ?? string.Empty).ToUpper().Contains(normalizedFilterValue)),
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
            case "staffpositionid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.StaffPositionId == parsedGuid);
                }
                break;
            }
            case "userid":
            {
                if (Guid.TryParse(filter.Value, out var parsedGuid))
                {
                    query = query.Where(item => item.UserId == parsedGuid);
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

    private static IOrderedQueryable<StaffPositionAssignment> ApplySort(
        IQueryable<StaffPositionAssignment> query,
        IReadOnlyList<ListStaffPositionAssignmentSort>? sortItems)
    {
        IOrderedQueryable<StaffPositionAssignment>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListStaffPositionAssignmentSort>())
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
            case "userid":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.UserId) : query.OrderBy(item => item.UserId))
                    : (descending ? ordered.ThenByDescending(item => item.UserId) : ordered.ThenBy(item => item.UserId));
                break;
            case "assignmentkind":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.AssignmentKind) : query.OrderBy(item => item.AssignmentKind))
                    : (descending ? ordered.ThenByDescending(item => item.AssignmentKind) : ordered.ThenBy(item => item.AssignmentKind));
                break;
            case "startsat":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.StartsAt) : query.OrderBy(item => item.StartsAt))
                    : (descending ? ordered.ThenByDescending(item => item.StartsAt) : ordered.ThenBy(item => item.StartsAt));
                break;
            case "endsat":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.EndsAt) : query.OrderBy(item => item.EndsAt))
                    : (descending ? ordered.ThenByDescending(item => item.EndsAt) : ordered.ThenBy(item => item.EndsAt));
                break;
            case "startsatutc":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.StartsAtUtc) : query.OrderBy(item => item.StartsAtUtc))
                    : (descending ? ordered.ThenByDescending(item => item.StartsAtUtc) : ordered.ThenBy(item => item.StartsAtUtc));
                break;
            case "endsatutc":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.EndsAtUtc) : query.OrderBy(item => item.EndsAtUtc))
                    : (descending ? ordered.ThenByDescending(item => item.EndsAtUtc) : ordered.ThenBy(item => item.EndsAtUtc));
                break;
            case "isactive":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.IsActive) : query.OrderBy(item => item.IsActive))
                    : (descending ? ordered.ThenByDescending(item => item.IsActive) : ordered.ThenBy(item => item.IsActive));
                break;
            case "reason":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Reason) : query.OrderBy(item => item.Reason))
                    : (descending ? ordered.ThenByDescending(item => item.Reason) : ordered.ThenBy(item => item.Reason));
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

    private static bool HasMeaningfulFilter(ListStaffPositionAssignmentFilter filter)
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

    private static bool IsPrimaryAssignment(string assignmentKind)
    {
        return string.Equals(
            assignmentKind.Trim(),
            "Primary",
            StringComparison.OrdinalIgnoreCase);
    }

    private static DateTime AssignmentIntervalEnd(DateTime? endsAt)
    {
        return endsAt ?? DateTime.MaxValue;
    }
}
