#nullable enable

using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Auth;

public sealed class AdminUserService
{
    private static readonly IReadOnlyList<EffectiveAccessRule> EffectiveAccessRules = new[]
    {
        new EffectiveAccessRule("Document", "Create", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("Document", "Delete", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("Document", "Read", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("Document", "Update", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentFragment", "Create", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentFragment", "Delete", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentFragment", "Read", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentFragment", "Update", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentRevision", "Create", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentRevision", "Delete", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentRevision", "Read", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("DocumentRevision", "Update", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("ProcessingJob", "Create", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("ProcessingJob", "Delete", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("ProcessingJob", "Read", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("ProcessingJob", "Update", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("StoredObject", "Create", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("StoredObject", "Delete", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("StoredObject", "Read", "Role", "DocumentEvidenceAdmin", "All", ""),
        new EffectiveAccessRule("StoredObject", "Update", "Role", "DocumentEvidenceAdmin", "All", ""),
    };

    private readonly DocumentEvidenceOperationalModelDbContext _db;
    private readonly IAppEmailSender _email;
    private readonly IConfiguration _configuration;
    private readonly IdentityAuditService _audit;

    public AdminUserService(
        DocumentEvidenceOperationalModelDbContext db,
        IAppEmailSender email,
        IConfiguration configuration,
        IdentityAuditService audit)
    {
        _db = db;
        _email = email;
        _configuration = configuration;
        _audit = audit;
    }

    public async Task<IReadOnlyList<AdminUserDto>> ListUsersAsync(string? query, CancellationToken ct)
    {
        var usersQuery = _db.AppUsers.AsQueryable();
        var search = query?.Trim();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var pattern = "%" + search + "%";
            usersQuery = usersQuery.Where(x =>
                EF.Functions.Like(x.Email, pattern)
                || EF.Functions.Like(x.UserName, pattern));
        }

        var users = await usersQuery
            .OrderBy(x => x.Email)
            .Take(200)
            .ToListAsync(ct);

        var result = new List<AdminUserDto>();
        foreach (var user in users)
        {
            result.Add(new AdminUserDto
            {
                Id = user.Id,
                Email = user.Email,
                UserName = user.UserName,
                IsActive = user.IsActive,
                MustChangePassword = user.MustChangePassword,
                EmailConfirmed = user.EmailConfirmed,
                Roles = await UserRoles(user.Id).ToArrayAsync(ct),
                StaffPositions = await ListStaffPositionAssignmentsAsync(user.Id, currentOnly: true, ct),
            });
        }
        return result;
    }

    public async Task<AdminEffectiveAccessDto?> GetEffectiveAccessAsync(Guid userId, CancellationToken ct)
    {
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == userId, ct);
        if (user is null)
        {
            return null;
        }

        var directRoles = await UserRoles(user.Id).ToArrayAsync(ct);
        var staffRoleCodes = await ActiveStaffPositionRoleCodes(user.Id).ToArrayAsync(ct);
        var allAssignments = await ListStaffPositionAssignmentsAsync(user.Id, currentOnly: false, ct);
        var activeAssignments = allAssignments.Where(x => x.IsCurrent).ToArray();
        var authenticatedPublicAccess = user.IsActive && user.EmailConfirmed;
        var directRoleSet = directRoles.ToHashSet(StringComparer.OrdinalIgnoreCase);
        var effectiveRoleSet = directRoles.Concat(staffRoleCodes).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var activeStaffPositionSet = activeAssignments
            .Select(x => x.StaffPositionCode)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        var warnings = BuildEffectiveAccessWarnings(user, allAssignments);
        var permissions = new SortedDictionary<string, EffectivePermissionAccumulator>(StringComparer.OrdinalIgnoreCase);

        foreach (var rule in EffectiveAccessRules)
        {
            var via = MatchEffectiveAccessRule(
                rule,
                authenticatedPublicAccess,
                directRoleSet,
                effectiveRoleSet,
                activeStaffPositionSet);
            if (via is null)
            {
                continue;
            }

            if (!permissions.TryGetValue(rule.PermissionCode, out var accumulator))
            {
                accumulator = new EffectivePermissionAccumulator(rule.EntityName, rule.Operation);
                permissions.Add(rule.PermissionCode, accumulator);
            }

            accumulator.Sources.Add(new AdminEffectiveAccessSourceDto
            {
                Audience = rule.Audience,
                Subject = rule.Subject,
                Scope = rule.Scope,
                OwnerField = rule.OwnerField,
                Via = via,
            });
        }

        return new AdminEffectiveAccessDto
        {
            UserId = user.Id,
            Email = user.Email,
            UserName = user.UserName,
            IsActive = user.IsActive,
            EmailConfirmed = user.EmailConfirmed,
            AuthenticatedPublicAccess = authenticatedPublicAccess,
            DirectRoles = directRoles,
            EffectiveRoles = effectiveRoleSet.OrderBy(x => x).ToArray(),
            ActiveStaffPositions = activeAssignments,
            EffectivePermissions = permissions
                .Select(pair => new AdminEffectivePermissionDto
                {
                    PermissionCode = pair.Key,
                    EntityName = pair.Value.EntityName,
                    Operation = pair.Value.Operation,
                    Sources = pair.Value.Sources
                        .OrderBy(x => x.Audience)
                        .ThenBy(x => x.Subject)
                        .ThenBy(x => x.Scope)
                        .ToArray(),
                })
                .ToArray(),
            Warnings = warnings,
        };
    }

    public async Task<AdminUserDto?> CreateUserAsync(CreateAdminUserRequest request, CancellationToken ct)
    {
        var email = request.Email.Trim();
        if (email.Length == 0 || request.Password.Length < 8)
        {
            return null;
        }
        if (await _db.AppUsers.AnyAsync(x => x.Email == email, ct))
        {
            return null;
        }

        var now = DateTime.UtcNow;
        var user = new AppUser
        {
            Id = Guid.NewGuid(),
            Email = email,
            UserName = email,
            EmailConfirmed = false,
            IsActive = true,
            MustChangePassword = request.MustChangePassword,
            CreatedAtUtc = now,
            UpdatedAtUtc = now,
        };
        user.PasswordHash = new PasswordHasher<AppUser>().HashPassword(user, request.Password);
        _db.AppUsers.Add(user);

        foreach (var roleCode in request.Roles.Distinct(StringComparer.OrdinalIgnoreCase))
        {
            await AssignRoleCoreAsync(user.Id, roleCode, ct);
        }
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.User.Create", user.Id, user.Email, "roles=" + string.Join(",", request.Roles), ct);
        return (await ListUsersAsync(null, ct)).Single(x => x.Id == user.Id);
    }

    public async Task<IReadOnlyList<AdminEmailConfirmationDto>> ListEmailConfirmationsAsync(CancellationToken ct)
    {
        var users = await _db.AppUsers.OrderBy(x => x.Email).ToListAsync(ct);
        var result = new List<AdminEmailConfirmationDto>();
        var now = DateTime.UtcNow;
        foreach (var user in users)
        {
            var latest = await _db.EmailConfirmationTokens
                .Where(x => x.AppUserId == user.Id)
                .OrderByDescending(x => x.CreatedAtUtc)
                .FirstOrDefaultAsync(ct);
            result.Add(new AdminEmailConfirmationDto
            {
                UserId = user.Id,
                Email = user.Email,
                UserName = user.UserName,
                IsActive = user.IsActive,
                EmailConfirmed = user.EmailConfirmed,
                LastSentAtUtc = latest?.CreatedAtUtc,
                LastExpiresAtUtc = latest?.ExpiresAtUtc,
                LastCompletedAtUtc = latest?.UsedAtUtc,
                HasPendingToken = latest is not null && latest.UsedAtUtc is null && latest.ExpiresAtUtc > now,
                CanSend = user.IsActive && !user.EmailConfirmed,
            });
        }
        return result;
    }

    public async Task<bool> SendEmailConfirmationAsync(Guid userId, CancellationToken ct)
    {
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == userId && x.IsActive, ct);
        if (user is null || user.EmailConfirmed)
        {
            return false;
        }
        var code = AuthCodeDigest.NewCode(32);
        var now = DateTime.UtcNow;
        var expiresAtUtc = now.AddHours(24);
        _db.EmailConfirmationTokens.Add(new EmailConfirmationToken
        {
            Id = Guid.NewGuid(),
            AppUserId = user.Id,
            TokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.ConfirmationPurpose, code),
            ExpiresAtUtc = expiresAtUtc,
            CreatedAtUtc = now,
        });
        await _db.SaveChangesAsync(ct);
        await _email.SendAsync(AppEmailTemplates.EmailConfirmation(
            AppEmailTemplates.ReadOptions(_configuration),
            user.Email,
            code,
            expiresAtUtc), ct);
        await _audit.RecordAsync("Identity.EmailConfirmation.Send", user.Id, user.Email, "expiresAtUtc=" + expiresAtUtc.ToString("O"), ct);
        return true;
    }

    public async Task<IReadOnlyList<AdminUserInvitationDto>> ListInvitationsAsync(CancellationToken ct)
    {
        var invitations = await _db.UserInvitations
            .OrderByDescending(x => x.CreatedAtUtc)
            .ToListAsync(ct);
        return invitations.Select(ToInvitationDto).ToArray();
    }

    public async Task<AdminUserInvitationDto?> CreateInvitationAsync(CreateUserInvitationRequest request, CancellationToken ct)
    {
        var email = request.Email.Trim();
        if (email.Length == 0 || await _db.AppUsers.AnyAsync(x => x.Email == email, ct))
        {
            return null;
        }

        var roleCodes = request.Roles.Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
        foreach (var roleCode in roleCodes)
        {
            if (!await _db.Roles.AnyAsync(x => x.Code == roleCode.Trim(), ct))
            {
                return null;
            }
        }

        var code = AuthCodeDigest.NewCode(32);
        var now = DateTime.UtcNow;
        var invitation = new UserInvitation
        {
            Id = Guid.NewGuid(),
            Email = email,
            TokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.InvitationPurpose, code),
            RoleCodes = string.Join("|", roleCodes),
            ExpiresAtUtc = now.AddDays(7),
            CreatedAtUtc = now,
        };
        _db.UserInvitations.Add(invitation);
        await _db.SaveChangesAsync(ct);
        await SendInvitationEmailAsync(invitation.Email, code, invitation.ExpiresAtUtc, roleCodes, ct);
        await _audit.RecordAsync("Identity.Invitation.Create", null, invitation.Email, "roles=" + string.Join(",", roleCodes), ct);
        return ToInvitationDto(invitation);
    }

    public async Task<AdminUserInvitationDto?> ResendInvitationAsync(Guid invitationId, CancellationToken ct)
    {
        var invitation = await _db.UserInvitations.SingleOrDefaultAsync(x => x.Id == invitationId, ct);
        if (invitation is null || invitation.AcceptedAtUtc is not null)
        {
            return null;
        }
        if (await _db.AppUsers.AnyAsync(x => x.Email == invitation.Email, ct))
        {
            return null;
        }

        var code = AuthCodeDigest.NewCode(32);
        invitation.TokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.InvitationPurpose, code);
        invitation.ExpiresAtUtc = DateTime.UtcNow.AddDays(7);
        await _db.SaveChangesAsync(ct);
        await SendInvitationEmailAsync(
            invitation.Email,
            code,
            invitation.ExpiresAtUtc,
            invitation.RoleCodes.Split('|', StringSplitOptions.RemoveEmptyEntries),
            ct);
        await _audit.RecordAsync("Identity.Invitation.Resend", null, invitation.Email, "invitationId=" + invitation.Id, ct);
        return ToInvitationDto(invitation);
    }

    public async Task<IReadOnlyList<AdminRoleDto>> ListRolesAsync(CancellationToken ct)
    {
        var roles = await _db.Roles.OrderBy(x => x.Code).ToListAsync(ct);
        var result = new List<AdminRoleDto>();
        foreach (var role in roles)
        {
            var permissions = await _db.RolePermissions
                .Where(x => x.RoleId == role.Id)
                .Join(_db.Permissions, x => x.PermissionId, x => x.Id, (_, permission) => permission.Code)
                .Distinct()
                .OrderBy(x => x)
                .ToArrayAsync(ct);
            result.Add(new AdminRoleDto
            {
                Id = role.Id,
                Code = role.Code,
                Name = role.Name,
                Permissions = permissions,
            });
        }
        return result;
    }

    public async Task<bool> AssignRoleAsync(Guid userId, string roleCode, CancellationToken ct)
    {
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == userId, ct);
        if (user is null || !await AssignRoleCoreAsync(userId, roleCode, ct))
        {
            return false;
        }
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.Role.Assign", user.Id, user.Email, "role=" + roleCode.Trim(), ct);
        return true;
    }

    public async Task<IReadOnlyList<AdminStaffPositionDto>> ListStaffPositionsAsync(CancellationToken ct)
    {
        return await _db.StaffPositions
            .OrderBy(x => x.Code)
            .Select(x => new AdminStaffPositionDto
            {
                Id = x.Id,
                Code = x.Code,
                Name = x.Name,
                Description = x.Description,
                IsActive = x.IsActive,
            })
            .ToArrayAsync(ct);
    }

    public async Task<IReadOnlyList<AdminStaffPositionAssignmentDto>> ListStaffPositionAssignmentsAsync(
        Guid? userId,
        bool currentOnly,
        CancellationToken ct)
    {
        var now = DateTime.UtcNow;
        var query = StaffAssignmentRows();
        if (userId.HasValue)
        {
            query = query.Where(x => x.Assignment.UserId == userId.Value);
        }
        if (currentOnly)
        {
            query = query.Where(x =>
                x.Assignment.IsActive
                && x.Position.IsActive
                && x.Assignment.StartsAt <= now
                && (!x.Assignment.EndsAt.HasValue || x.Assignment.EndsAt.Value > now));
        }

        var rows = await query
            .OrderBy(x => x.User.Email)
            .ThenBy(x => x.Position.Code)
            .ThenByDescending(x => x.Assignment.StartsAt)
            .Take(500)
            .ToListAsync(ct);
        return rows.Select(x => ToStaffAssignmentDto(x.Assignment, x.User, x.Position, now)).ToArray();
    }

    public async Task<AdminStaffPositionAssignmentDto?> AssignStaffPositionAsync(
        Guid userId,
        AssignStaffPositionRequest request,
        CancellationToken ct)
    {
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == userId && x.IsActive, ct);
        var positionCode = request.StaffPositionCode.Trim();
        var position = await _db.StaffPositions.SingleOrDefaultAsync(x => x.Code == positionCode && x.IsActive, ct);
        if (user is null || position is null)
        {
            return null;
        }

        var startsAt = request.StartsAtUtc ?? DateTime.UtcNow;
        if (request.EndsAtUtc.HasValue && request.EndsAtUtc.Value <= startsAt)
        {
            return null;
        }

        var alreadyAssigned = await _db.StaffPositionAssignments.AnyAsync(x =>
            x.UserId == user.Id
            && x.StaffPositionId == position.Id
            && x.IsActive
            && x.StartsAt <= startsAt
            && (!x.EndsAt.HasValue || x.EndsAt.Value > startsAt), ct);
        if (alreadyAssigned)
        {
            return null;
        }

        var assignment = new StaffPositionAssignment
        {
            Id = Guid.NewGuid(),
            UserId = user.Id,
            StaffPositionId = position.Id,
            AssignmentKind = Clip(DefaultIfBlank(request.AssignmentKind, "Primary"), 32),
            StartsAt = startsAt,
            EndsAt = request.EndsAtUtc,
            IsActive = true,
            Reason = Clip(request.Reason.Trim(), 500),
        };
        _db.StaffPositionAssignments.Add(assignment);
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync(
            "Identity.StaffPosition.Assign",
            user.Id,
            user.Email,
            $"position={position.Code};kind={assignment.AssignmentKind};startsAt={assignment.StartsAt:O};endsAt={assignment.EndsAt:O};reason={assignment.Reason}",
            ct);
        return ToStaffAssignmentDto(assignment, user, position, DateTime.UtcNow);
    }

    public async Task<AdminStaffPositionAssignmentDto?> CloseStaffPositionAssignmentAsync(
        Guid assignmentId,
        CloseStaffPositionAssignmentRequest request,
        CancellationToken ct)
    {
        var row = await StaffAssignmentRows().SingleOrDefaultAsync(x => x.Assignment.Id == assignmentId, ct);
        if (row is null)
        {
            return null;
        }

        CloseAssignment(row.Assignment, request);
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync(
            "Identity.StaffPosition.Close",
            row.User.Id,
            row.User.Email,
            $"position={row.Position.Code};assignmentId={row.Assignment.Id};endsAt={row.Assignment.EndsAt:O};reason={row.Assignment.Reason}",
            ct);
        return ToStaffAssignmentDto(row.Assignment, row.User, row.Position, DateTime.UtcNow);
    }

    public async Task<IReadOnlyList<AdminStaffPositionAssignmentDto>> CloseUserStaffPositionAssignmentsAsync(
        Guid userId,
        CloseStaffPositionAssignmentRequest request,
        CancellationToken ct)
    {
        var now = DateTime.UtcNow;
        var rows = await StaffAssignmentRows()
            .Where(x =>
                x.User.Id == userId
                && x.Assignment.IsActive
                && x.Assignment.StartsAt <= now
                && (!x.Assignment.EndsAt.HasValue || x.Assignment.EndsAt.Value > now))
            .ToListAsync(ct);
        foreach (var row in rows)
        {
            CloseAssignment(row.Assignment, request);
        }
        await _db.SaveChangesAsync(ct);

        if (rows.Count > 0)
        {
            var user = rows[0].User;
            await _audit.RecordAsync(
                "Identity.StaffPosition.Offboard",
                user.Id,
                user.Email,
                "closed=" + string.Join(",", rows.Select(x => x.Position.Code)),
                ct);
        }

        return rows.Select(x => ToStaffAssignmentDto(x.Assignment, x.User, x.Position, DateTime.UtcNow)).ToArray();
    }

    private async Task<bool> AssignRoleCoreAsync(Guid userId, string roleCode, CancellationToken ct)
    {
        var role = await _db.Roles.SingleOrDefaultAsync(x => x.Code == roleCode.Trim(), ct);
        if (role is null)
        {
            return false;
        }
        var hasRole = await _db.AppUserRoles.AnyAsync(x => x.AppUserId == userId && x.RoleId == role.Id, ct);
        if (!hasRole)
        {
            _db.AppUserRoles.Add(new AppUserRole { Id = Guid.NewGuid(), AppUserId = userId, RoleId = role.Id });
        }
        return true;
    }

    private IQueryable<string> UserRoles(Guid userId)
    {
        return _db.AppUserRoles
            .Where(x => x.AppUserId == userId)
            .Join(_db.Roles, x => x.RoleId, x => x.Id, (_, role) => role.Code)
            .Distinct()
            .OrderBy(x => x);
    }

    private IQueryable<string> ActiveStaffPositionRoleCodes(Guid userId)
    {
        var now = DateTime.UtcNow;
        return _db.StaffPositionAssignments
            .Where(assignment =>
                assignment.UserId == userId
                && assignment.IsActive
                && assignment.StartsAt <= now
                && (!assignment.EndsAt.HasValue || assignment.EndsAt.Value > now))
            .Join(_db.StaffPositions.Where(position => position.IsActive),
                assignment => assignment.StaffPositionId,
                position => position.Id,
                (assignment, position) => position)
            .Join(_db.StaffPositionRoles,
                position => position.Id,
                positionRole => positionRole.StaffPositionId,
                (_, positionRole) => positionRole)
            .Join(_db.Roles,
                positionRole => positionRole.RoleId,
                role => role.Id,
                (_, role) => role.Code)
            .Distinct()
            .OrderBy(x => x);
    }

    private static string? MatchEffectiveAccessRule(
        EffectiveAccessRule rule,
        bool authenticatedPublicAccess,
        HashSet<string> directRoles,
        HashSet<string> effectiveRoles,
        HashSet<string> activeStaffPositions)
    {
        if (rule.Audience.Equals("Authenticated", StringComparison.OrdinalIgnoreCase))
        {
            return authenticatedPublicAccess ? "authenticated-user" : null;
        }
        if (rule.Audience.Equals("StaffPosition", StringComparison.OrdinalIgnoreCase))
        {
            return activeStaffPositions.Contains(rule.Subject) ? "active-staff-position" : null;
        }
        if (rule.Audience.Equals("Role", StringComparison.OrdinalIgnoreCase))
        {
            if (directRoles.Contains(rule.Subject))
            {
                return "direct-role";
            }
            return effectiveRoles.Contains(rule.Subject) ? "staff-position-role" : null;
        }
        return null;
    }

    private static IReadOnlyList<string> BuildEffectiveAccessWarnings(
        AppUser user,
        IReadOnlyList<AdminStaffPositionAssignmentDto> assignments)
    {
        var warnings = new List<string>();
        if (!user.IsActive)
        {
            warnings.Add("user-inactive");
        }
        if (!user.EmailConfirmed)
        {
            warnings.Add("email-not-confirmed");
        }
        if (!assignments.Any(x => x.IsCurrent))
        {
            warnings.Add("no-active-staff-position");
        }
        if (assignments.Any(x => !x.IsActive))
        {
            warnings.Add("inactive-staff-assignment");
        }
        if (assignments.Any(x => x.EndsAtUtc.HasValue && x.EndsAtUtc.Value <= DateTime.UtcNow))
        {
            warnings.Add("expired-staff-assignment");
        }
        return warnings;
    }

    private IQueryable<StaffAssignmentRow> StaffAssignmentRows()
    {
        return _db.StaffPositionAssignments
            .Join(_db.AppUsers, assignment => assignment.UserId, user => user.Id, (assignment, user) => new { assignment, user })
            .Join(
                _db.StaffPositions,
                row => row.assignment.StaffPositionId,
                position => position.Id,
                (row, position) => new StaffAssignmentRow(row.assignment, row.user, position));
    }

    private static void CloseAssignment(
        StaffPositionAssignment assignment,
        CloseStaffPositionAssignmentRequest request)
    {
        var requestedEndsAt = request.EndsAtUtc ?? DateTime.UtcNow;
        assignment.EndsAt = requestedEndsAt < assignment.StartsAt ? assignment.StartsAt : requestedEndsAt;
        assignment.IsActive = false;
        var reason = request.Reason.Trim();
        if (reason.Length > 0)
        {
            assignment.Reason = Clip(reason, 500);
        }
    }

    private static AdminStaffPositionAssignmentDto ToStaffAssignmentDto(
        StaffPositionAssignment assignment,
        AppUser user,
        StaffPosition position,
        DateTime now)
    {
        return new AdminStaffPositionAssignmentDto
        {
            Id = assignment.Id,
            UserId = user.Id,
            UserEmail = user.Email,
            StaffPositionId = position.Id,
            StaffPositionCode = position.Code,
            StaffPositionName = position.Name,
            AssignmentKind = assignment.AssignmentKind,
            StartsAtUtc = assignment.StartsAt,
            EndsAtUtc = assignment.EndsAt,
            IsActive = assignment.IsActive,
            IsCurrent = assignment.IsActive
                && position.IsActive
                && assignment.StartsAt <= now
                && (!assignment.EndsAt.HasValue || assignment.EndsAt.Value > now),
            Reason = assignment.Reason,
        };
    }

    private static AdminUserInvitationDto ToInvitationDto(UserInvitation invitation)
    {
        var now = DateTime.UtcNow;
        return new AdminUserInvitationDto
        {
            Id = invitation.Id,
            Email = invitation.Email,
            ExpiresAtUtc = invitation.ExpiresAtUtc,
            AcceptedAtUtc = invitation.AcceptedAtUtc,
            IsExpired = invitation.AcceptedAtUtc is null && invitation.ExpiresAtUtc <= now,
            CanResend = invitation.AcceptedAtUtc is null,
            Roles = invitation.RoleCodes.Split('|', StringSplitOptions.RemoveEmptyEntries),
        };
    }

    private async Task SendInvitationEmailAsync(
        string email,
        string code,
        DateTime expiresAtUtc,
        IReadOnlyList<string> roles,
        CancellationToken ct)
    {
        await _email.SendAsync(AppEmailTemplates.Invitation(
            AppEmailTemplates.ReadOptions(_configuration),
            email,
            code,
            expiresAtUtc,
            roles), ct);
    }

    private static string DefaultIfBlank(string value, string defaultValue)
    {
        return string.IsNullOrWhiteSpace(value) ? defaultValue : value.Trim();
    }

    private static string Clip(string value, int maxLength)
    {
        return value.Length <= maxLength ? value : value[..maxLength];
    }

    private sealed class EffectivePermissionAccumulator
    {
        public EffectivePermissionAccumulator(string entityName, string operation)
        {
            EntityName = entityName;
            Operation = operation;
        }

        public string EntityName { get; }
        public string Operation { get; }
        public List<AdminEffectiveAccessSourceDto> Sources { get; } = new();
    }

    private sealed record EffectiveAccessRule(
        string EntityName,
        string Operation,
        string Audience,
        string Subject,
        string Scope,
        string OwnerField)
    {
        public string PermissionCode => EntityName + "." + Operation;
    }

    private sealed record StaffAssignmentRow(
        StaffPositionAssignment Assignment,
        AppUser User,
        StaffPosition Position);
}
