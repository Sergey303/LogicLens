#nullable enable

using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Api.Services;

public sealed class ProcessingJobService
{
    private const int MaxPageSize = 100;
    private const int MaxSuggestionCount = 20;
    private readonly DocumentEvidenceOperationalModelDbContext _db;

    public ProcessingJobService(DocumentEvidenceOperationalModelDbContext db)
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

    public async Task<ListProcessingJobResult> ListAsync(
        ListProcessingJobRequest request,
        Func<IQueryable<ProcessingJob>, IQueryable<ProcessingJob>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var page = NormalizePage(request.Page);
        var pageSize = NormalizePageSize(request.PageSize);
        IQueryable<ProcessingJob> query = _db.ProcessingJobs.AsNoTracking();
        query = authorizeQuery(query);
        query = ApplyFilters(query, request.Filters);
        var totalCount = await query.CountAsync(cancellationToken);
        var entities = await ApplySort(query, request.Sort)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        return new ListProcessingJobResult
        {
            Items = entities.Select(ToDto).ToList(),
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
        };
    }

    public async Task<ProcessingJob?> GetAsync(
        Guid id,
        bool asNoTracking,
        CancellationToken cancellationToken)
    {
        IQueryable<ProcessingJob> query = _db.ProcessingJobs;
        if (asNoTracking)
        {
            query = query.AsNoTracking();
        }

        return await query.FirstOrDefaultAsync(item => item.Id == id, cancellationToken);
    }

    public async Task<IReadOnlyList<ProcessingJobLookupDto>> LookupAsync(
        LookupProcessingJobRequest request,
        Func<IQueryable<ProcessingJob>, IQueryable<ProcessingJob>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.ProcessingJobs.AsNoTracking();
        query = authorizeQuery(query);
        if (normalizedQuery.Length > 0)
        {
            query = query.Where(item => item.KindSearch.Contains(normalizedQuery));
        }
        query = query.OrderBy(item => item.Kind);

        return await query
            .Take(take)
            .Select(item => new ProcessingJobLookupDto
            {
                Value = item.Id.ToString(),
                Label = item.Kind,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<ProcessingJobSuggestionDto>> SuggestAsync(
        string field,
        SuggestProcessingJobRequest request,
        Func<IQueryable<ProcessingJob>, IQueryable<ProcessingJob>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var normalizedQuery = NormalizeSearchValue(request.Query);
        var take = Math.Clamp(request.Take, 1, MaxSuggestionCount);
        var query = _db.ProcessingJobs.AsNoTracking();
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
                    .Select(value => new ProcessingJobSuggestionDto
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
                    .Select(value => new ProcessingJobSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "idempotencykey":
                return await query
                    .Where(item => item.IdempotencyKey != null)
                    .Where(item => normalizedQuery.Length == 0 || item.IdempotencyKeySearch.Contains(normalizedQuery))
                    .Select(item => item.IdempotencyKey!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new ProcessingJobSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "lasterrorcode":
                return await query
                    .Where(item => item.LastErrorCode != null)
                    .Where(item => normalizedQuery.Length == 0 || item.LastErrorCodeSearch.Contains(normalizedQuery))
                    .Select(item => item.LastErrorCode!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Take(take)
                    .Select(value => new ProcessingJobSuggestionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<ProcessingJobSuggestionDto>();
    }

    public async Task<IReadOnlyList<ProcessingJobOptionDto>> OptionsAsync(
        string field,
        Func<IQueryable<ProcessingJob>, IQueryable<ProcessingJob>> authorizeQuery,
        CancellationToken cancellationToken)
    {
        var query = _db.ProcessingJobs.AsNoTracking();
        query = authorizeQuery(query);
        switch (NormalizeField(field))
        {
            case "kind":
                return await query
                    .Where(item => item.Kind != null)
                    .Select(item => item.Kind!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Select(value => new ProcessingJobOptionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            case "state":
                return await query
                    .Where(item => item.State != null)
                    .Select(item => item.State!)
                    .Distinct()
                    .OrderBy(value => value)
                    .Select(value => new ProcessingJobOptionDto
                    {
                        Value = value,
                        Label = value,
                    })
                    .ToListAsync(cancellationToken);
            default:
                break;
        }

        return Array.Empty<ProcessingJobOptionDto>();
    }

    public async Task<ProcessingJob> CreateAsync(
        CreateProcessingJobRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        var entity = new ProcessingJob
        {
            Id = Guid.NewGuid(),
            DocumentRevisionId = request.DocumentRevisionId,
            Kind = request.Kind,
            State = request.State,
            Attempt = request.Attempt,
            IdempotencyKey = request.IdempotencyKey,
            LeaseUntil = request.LeaseUntil,
            LastErrorCode = request.LastErrorCode,
            CreationTime = DateTime.UtcNow,
            CreatorId = currentUserId,
            CreatorPositionId = currentAuditPositionId,
            IsDeleted = false,
            KindSearch = NormalizeSearchValue(request.Kind),
            StateSearch = NormalizeSearchValue(request.State),
            IdempotencyKeySearch = NormalizeSearchValue(request.IdempotencyKey),
            LastErrorCodeSearch = NormalizeSearchValue(request.LastErrorCode),
        };

        _db.ProcessingJobs.Add(entity);
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task<ProcessingJob> UpdateAsync(
        ProcessingJob entity,
        UpdateProcessingJobRequest request,
        Guid? currentUserId,
        Guid? currentAuditPositionId,
        CancellationToken cancellationToken)
    {
        entity.DocumentRevisionId = request.DocumentRevisionId;
        entity.Kind = request.Kind;
        entity.State = request.State;
        entity.Attempt = request.Attempt;
        entity.IdempotencyKey = request.IdempotencyKey;
        entity.LeaseUntil = request.LeaseUntil;
        entity.LastErrorCode = request.LastErrorCode;
        entity.KindSearch = NormalizeSearchValue(request.Kind);
        entity.StateSearch = NormalizeSearchValue(request.State);
        entity.IdempotencyKeySearch = NormalizeSearchValue(request.IdempotencyKey);
        entity.LastErrorCodeSearch = NormalizeSearchValue(request.LastErrorCode);
        entity.LastModificationTime = DateTime.UtcNow;
        entity.LastModifierId = currentUserId;
        entity.LastModifierPositionId = currentAuditPositionId;
        await _db.SaveChangesAsync(cancellationToken);

        return entity;
    }

    public async Task DeleteAsync(
        ProcessingJob entity,
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
        ProcessingJob entity,
        CancellationToken cancellationToken)
    {
        return Array.Empty<string>();
    }

    public ProcessingJobDto ToDto(ProcessingJob entity)
    {
        return new ProcessingJobDto
        {
            Id = entity.Id,
            DocumentRevisionId = entity.DocumentRevisionId,
            Kind = entity.Kind,
            State = entity.State,
            Attempt = entity.Attempt,
            IdempotencyKey = entity.IdempotencyKey,
            LeaseUntil = entity.LeaseUntil,
            LastErrorCode = entity.LastErrorCode,
        };
    }

    private static IQueryable<ProcessingJob> ApplyFilters(
        IQueryable<ProcessingJob> query,
        IReadOnlyList<ListProcessingJobFilter>? filters)
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
            case "idempotencykey":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.IdempotencyKeySearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.IdempotencyKeySearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.IdempotencyKeySearch.Contains(normalizedFilterValue)),
                };
                break;
            case "lasterrorcode":
                if (normalizedFilterValue.Length == 0)
                {
                    break;
                }
                query = filterOperator switch
                {
                    "equals" => query.Where(item => item.LastErrorCodeSearch == normalizedFilterValue),
                    "startsWith" => query.Where(item => item.LastErrorCodeSearch.StartsWith(normalizedFilterValue)),
                    _ => query.Where(item => item.LastErrorCodeSearch.Contains(normalizedFilterValue)),
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

    private static IOrderedQueryable<ProcessingJob> ApplySort(
        IQueryable<ProcessingJob> query,
        IReadOnlyList<ListProcessingJobSort>? sortItems)
    {
        IOrderedQueryable<ProcessingJob>? ordered = null;

        foreach (var sort in sortItems ?? Array.Empty<ListProcessingJobSort>())
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
            case "kind":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Kind) : query.OrderBy(item => item.Kind))
                    : (descending ? ordered.ThenByDescending(item => item.Kind) : ordered.ThenBy(item => item.Kind));
                break;
            case "state":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.State) : query.OrderBy(item => item.State))
                    : (descending ? ordered.ThenByDescending(item => item.State) : ordered.ThenBy(item => item.State));
                break;
            case "attempt":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.Attempt) : query.OrderBy(item => item.Attempt))
                    : (descending ? ordered.ThenByDescending(item => item.Attempt) : ordered.ThenBy(item => item.Attempt));
                break;
            case "idempotencykey":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.IdempotencyKey) : query.OrderBy(item => item.IdempotencyKey))
                    : (descending ? ordered.ThenByDescending(item => item.IdempotencyKey) : ordered.ThenBy(item => item.IdempotencyKey));
                break;
            case "leaseuntil":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.LeaseUntil) : query.OrderBy(item => item.LeaseUntil))
                    : (descending ? ordered.ThenByDescending(item => item.LeaseUntil) : ordered.ThenBy(item => item.LeaseUntil));
                break;
            case "lasterrorcode":
                ordered = ordered is null
                    ? (descending ? query.OrderByDescending(item => item.LastErrorCode) : query.OrderBy(item => item.LastErrorCode))
                    : (descending ? ordered.ThenByDescending(item => item.LastErrorCode) : ordered.ThenBy(item => item.LastErrorCode));
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

    private static bool HasMeaningfulFilter(ListProcessingJobFilter filter)
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
