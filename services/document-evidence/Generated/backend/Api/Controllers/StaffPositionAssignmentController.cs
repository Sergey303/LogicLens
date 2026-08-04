#nullable enable

using System.Security.Claims;
using ChatPilot.Api.FrontendActions;
using LogicLens.DocumentEvidence.Generated;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace LogicLens.DocumentEvidence.Generated.Api.Controllers;

[ApiController]
[RestCrudController("staff.position.assignment")] 
[Route("api/staffpositionassignments")]
public sealed class StaffPositionAssignmentController : ControllerBase
{
    private readonly StaffPositionAssignmentService _service;

    public StaffPositionAssignmentController(StaffPositionAssignmentService service)
    {
        _service = service;
    }

    [PolicyGate("StaffPositionAssignment.Read")]
    [HttpGet]
    public async Task<ActionResult<ListStaffPositionAssignmentResult>> List(
        [FromQuery] ListStaffPositionAssignmentRequest request,
        CancellationToken cancellationToken)
    {
        if (!CanRead())
        {
            return Forbid();
        }
        var result = await _service.ListAsync(request, ApplyReadRowAuthorization, cancellationToken);
        return Ok(result);
    }

    [PolicyGate("StaffPositionAssignment.Read")]
    [HttpGet("{id}")]
    public async Task<ActionResult<StaffPositionAssignmentDto>> Get(
        Guid id,
        CancellationToken cancellationToken)
    {
        var entity = await _service.GetAsync(id, asNoTracking: true, cancellationToken);
        if (entity is null)
        {
            return NotFound();
        }

        if (!CanRead())
        {
            return Forbid();
        }
        if (!CanAccessRead(entity))
        {
            return Forbid();
        }
        return Ok(_service.ToDto(entity));
    }

    [PolicyGate("StaffPositionAssignment.Read")]
    [HttpGet("lookup")]
    [ApiOperation(ApiOperationKind.Query)]
    [ProducesResponseType(typeof(IReadOnlyList<StaffPositionAssignmentLookupDto>), 200)]
    public async Task<ActionResult<IReadOnlyList<StaffPositionAssignmentLookupDto>>> Lookup(
        [FromQuery] LookupStaffPositionAssignmentRequest request,
        CancellationToken cancellationToken)
    {
        if (!CanRead())
        {
            return Forbid();
        }
        return Ok(await _service.LookupAsync(request, ApplyReadRowAuthorization, cancellationToken));
    }

    [PolicyGate("StaffPositionAssignment.Read")]
    [HttpGet("suggest/{field}")]
    [ApiOperation(ApiOperationKind.Query)]
    [ProducesResponseType(typeof(IReadOnlyList<StaffPositionAssignmentSuggestionDto>), 200)]
    public async Task<ActionResult<IReadOnlyList<StaffPositionAssignmentSuggestionDto>>> Suggest(
        string field,
        [FromQuery] SuggestStaffPositionAssignmentRequest request,
        CancellationToken cancellationToken)
    {
        if (!CanRead())
        {
            return Forbid();
        }
        return Ok(await _service.SuggestAsync(field, request, ApplyReadRowAuthorization, cancellationToken));
    }

    [PolicyGate("StaffPositionAssignment.Read")]
    [HttpGet("options/{field}")]
    [ApiOperation(ApiOperationKind.Query)]
    [ProducesResponseType(typeof(IReadOnlyList<StaffPositionAssignmentOptionDto>), 200)]
    public async Task<ActionResult<IReadOnlyList<StaffPositionAssignmentOptionDto>>> Options(
        string field,
        CancellationToken cancellationToken)
    {
        if (!CanRead())
        {
            return Forbid();
        }
        return Ok(await _service.OptionsAsync(field, ApplyReadRowAuthorization, cancellationToken));
    }

    [PolicyGate("StaffPositionAssignment.Create")]
    [HttpPost]
    public async Task<ActionResult<StaffPositionAssignmentDto>> Create(
        CreateStaffPositionAssignmentRequest request,
        CancellationToken cancellationToken)
    {
        if (!CanCreate())
        {
            return Forbid();
        }
        var entity = await _service.CreateAsync(
            request,
            GetCurrentUserId(),
            GetCurrentAuditPositionId(),
            cancellationToken);
        AddWarnings(await _service.GetMutationWarningsAsync(entity, cancellationToken));

        return CreatedAtAction(nameof(Get), new { id = entity.Id }, _service.ToDto(entity));
    }

    [PolicyGate("StaffPositionAssignment.Update")]
    [HttpPut("{id}")]
    public async Task<ActionResult<StaffPositionAssignmentDto>> Update(
        Guid id,
        UpdateStaffPositionAssignmentRequest request,
        CancellationToken cancellationToken)
    {
        var entity = await _service.GetAsync(id, asNoTracking: false, cancellationToken);
        if (entity is null)
        {
            return NotFound();
        }

        if (!CanUpdate())
        {
            return Forbid();
        }
        if (!CanAccessUpdate(entity))
        {
            return Forbid();
        }
        entity = await _service.UpdateAsync(
            entity,
            request,
            GetCurrentUserId(),
            GetCurrentAuditPositionId(),
            cancellationToken);
        AddWarnings(await _service.GetMutationWarningsAsync(entity, cancellationToken));

        return Ok(_service.ToDto(entity));
    }

    [PolicyGate("StaffPositionAssignment.Delete")]
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        var entity = await _service.GetAsync(id, asNoTracking: false, cancellationToken);
        if (entity is null)
        {
            return NotFound();
        }

        if (!CanDelete())
        {
            return Forbid();
        }
        if (!CanAccessDelete(entity))
        {
            return Forbid();
        }
        await _service.DeleteAsync(
            entity,
            GetCurrentUserId(),
            GetCurrentAuditPositionId(),
            cancellationToken);

        return NoContent();
    }

    private bool CanRead()
    {
        return HasPermission("StaffPositionAssignment.Read")
            || CanReadAll()
            || CanReadOwn();
    }

    private bool CanCreate()
    {
        return HasPermission("StaffPositionAssignment.Create")
            || CanCreateAll()
            || CanCreateOwn();
    }

    private bool CanUpdate()
    {
        return HasPermission("StaffPositionAssignment.Update")
            || CanUpdateAll()
            || CanUpdateOwn();
    }

    private bool CanDelete()
    {
        return HasPermission("StaffPositionAssignment.Delete")
            || CanDeleteAll()
            || CanDeleteOwn();
    }

    private bool CanReadAll()
    {
        return HasAnyRole("Admin");
    }

    private bool CanReadOwn()
    {
        return false;
    }

    private bool CanCreateAll()
    {
        return HasAnyRole("Admin");
    }

    private bool CanCreateOwn()
    {
        return false;
    }

    private bool CanUpdateAll()
    {
        return HasAnyRole("Admin");
    }

    private bool CanUpdateOwn()
    {
        return false;
    }

    private bool CanDeleteAll()
    {
        return HasAnyRole("Admin");
    }

    private bool CanDeleteOwn()
    {
        return false;
    }

    private IQueryable<StaffPositionAssignment> ApplyReadRowAuthorization(IQueryable<StaffPositionAssignment> query)
    {
        if (CanReadAll())
        {
            return query;
        }

        if (!CanReadOwn())
        {
            return query.Where(_ => false);
        }

        var ownIds = GetCurrentOwnIds();
        if (ownIds.Count == 0)
        {
            return query.Where(_ => false);
        }

        return query.Where(item => false);
    }

    private bool CanAccessRead(StaffPositionAssignment entity)
    {
        if (CanReadAll())
        {
            return true;
        }

        if (!CanReadOwn())
        {
            return false;
        }

        var ownIds = GetCurrentOwnIds();
        if (ownIds.Count == 0)
        {
            return false;
        }

        return false;
    }

    private bool CanAccessUpdate(StaffPositionAssignment entity)
    {
        if (CanUpdateAll())
        {
            return true;
        }

        if (!CanUpdateOwn())
        {
            return false;
        }

        var ownIds = GetCurrentOwnIds();
        if (ownIds.Count == 0)
        {
            return false;
        }

        return false;
    }

    private bool CanAccessDelete(StaffPositionAssignment entity)
    {
        if (CanDeleteAll())
        {
            return true;
        }

        if (!CanDeleteOwn())
        {
            return false;
        }

        var ownIds = GetCurrentOwnIds();
        if (ownIds.Count == 0)
        {
            return false;
        }

        return false;
    }

    private HashSet<Guid> GetCurrentOwnIds()
    {
        var ids = new HashSet<Guid>();
        var userId = GetCurrentUserId();
        if (userId.HasValue)
        {
            ids.Add(userId.Value);
            var now = DateTime.UtcNow;
            foreach (var positionId in ActiveStaffPositionAssignments(userId.Value, now)
                .Select(assignment => assignment.StaffPositionId)
                .Distinct())
            {
                ids.Add(positionId);
            }
        }

        AddClaimGuids(ids, "ownerId");
        AddClaimGuids(ids, "ownerIds");
        AddClaimGuids(ids, "positionId");
        AddClaimGuids(ids, "positionIds");
        AddClaimGuids(ids, "staffPositionId");
        AddClaimGuids(ids, "staffPositionIds");
        AddClaimGuids(ids, "staff_position");
        AddClaimGuids(ids, "staff_positions");

        return ids;
    }

    private Guid? GetCurrentAuditPositionId()
    {
        var claimPositionIds = new HashSet<Guid>();
        AddClaimGuids(claimPositionIds, "currentPositionId");
        AddClaimGuids(claimPositionIds, "currentStaffPositionId");
        AddClaimGuids(claimPositionIds, "positionId");
        AddClaimGuids(claimPositionIds, "staffPositionId");
        if (claimPositionIds.Count == 1)
        {
            return claimPositionIds.Single();
        }

        var userId = GetCurrentUserId();
        if (!userId.HasValue)
        {
            return null;
        }

        var now = DateTime.UtcNow;
        var activePositionIds = ActiveStaffPositionAssignments(userId.Value, now)
            .Select(assignment => assignment.StaffPositionId)
            .Distinct()
            .Take(2)
            .ToList();
        return activePositionIds.Count == 1 ? activePositionIds[0] : null;
    }

    private void AddClaimGuids(HashSet<Guid> ids, string claimType)
    {
        foreach (var claim in User.FindAll(claimType))
        {
            foreach (var rawValue in claim.Value.Split(' ', ',', ';'))
            {
                if (Guid.TryParse(rawValue.Trim(), out var id))
                {
                    ids.Add(id);
                }
            }
        }
    }

    private IQueryable<StaffPositionAssignment> ActiveStaffPositionAssignments(Guid userId, DateTime now)
    {
        return _service.ActiveStaffPositionAssignments(userId, now);
    }

    private bool IsAuthenticatedUser()
    {
        return User.Identity?.IsAuthenticated == true && GetCurrentUserId().HasValue;
    }

    private bool HasEffectiveRole(string roleCode)
    {
        var userId = GetCurrentUserId();
        if (!userId.HasValue)
        {
            return false;
        }

        var now = DateTime.UtcNow;
        return ActiveStaffPositionAssignments(userId.Value, now)
            .Any(assignment => assignment.StaffPosition.StaffPositionRoles
                .Any(positionRole => positionRole.Role.Code == roleCode));
    }

    private bool HasEffectivePermission(string permissionCode)
    {
        var userId = GetCurrentUserId();
        if (!userId.HasValue)
        {
            return false;
        }

        var now = DateTime.UtcNow;
        return ActiveStaffPositionAssignments(userId.Value, now)
            .Any(assignment => assignment.StaffPosition.StaffPositionRoles
                .Any(positionRole => positionRole.Role.RolePermissions
                    .Any(rolePermission => rolePermission.Permission.Code == permissionCode)));
    }

    private bool HasAnyActiveStaffPosition(params string[] positionCodes)
    {
        var userId = GetCurrentUserId();
        if (!userId.HasValue)
        {
            return false;
        }

        var requested = positionCodes.ToHashSet(StringComparer.OrdinalIgnoreCase);
        if (requested.Count == 0)
        {
            return false;
        }

        var now = DateTime.UtcNow;
        return ActiveStaffPositionAssignments(userId.Value, now)
            .Any(assignment => requested.Contains(assignment.StaffPosition.Code));
    }

    private bool HasAnyRole(params string[] roles)
    {
        foreach (var role in roles)
        {
            if (User.IsInRole(role)
                || HasClaimValue(ClaimTypes.Role, role)
                || HasClaimValue("role", role)
                || HasClaimValue("roles", role)
                || HasEffectiveRole(role))
            {
                return true;
            }
        }

        return false;
    }

    private bool HasPermission(string permissionCode)
    {
        return HasClaimValue("permission", permissionCode)
            || HasClaimValue("permissions", permissionCode)
            || HasClaimValue("scope", permissionCode)
            || HasEffectivePermission(permissionCode);
    }

    private bool HasClaimValue(string claimType, string expectedValue)
    {
        foreach (var claim in User.FindAll(claimType))
        {
            foreach (var value in claim.Value.Split(' ', ',', ';'))
            {
                if (string.Equals(value.Trim(), expectedValue, StringComparison.OrdinalIgnoreCase))
                {
                    return true;
                }
            }
        }

        return false;
    }

    private Guid? GetCurrentUserId()
    {
        var value = User.FindFirst(ClaimTypes.NameIdentifier)?.Value
            ?? User.FindFirst("sub")?.Value;
        return Guid.TryParse(value, out var userId) ? userId : null;
    }

    private void AddWarnings(IReadOnlyList<string> warnings)
    {
        if (warnings.Count > 0)
        {
            Response.Headers["X-AppForge-Warnings"] = string.Join(",", warnings);
        }
    }
}
