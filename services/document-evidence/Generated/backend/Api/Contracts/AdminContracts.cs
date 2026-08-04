#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class AdminUserDto
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public bool MustChangePassword { get; set; }
    public bool EmailConfirmed { get; set; }
    public IReadOnlyList<string> Roles { get; set; } = Array.Empty<string>();
    public IReadOnlyList<AdminStaffPositionAssignmentDto> StaffPositions { get; set; } = Array.Empty<AdminStaffPositionAssignmentDto>();
}

public sealed class AdminRoleDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public IReadOnlyList<string> Permissions { get; set; } = Array.Empty<string>();
}

public sealed class AdminStaffPositionDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public bool IsActive { get; set; }
}

public sealed class AdminStaffPositionAssignmentDto
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string UserEmail { get; set; } = string.Empty;
    public Guid StaffPositionId { get; set; }
    public string StaffPositionCode { get; set; } = string.Empty;
    public string StaffPositionName { get; set; } = string.Empty;
    public string AssignmentKind { get; set; } = string.Empty;
    public DateTime StartsAtUtc { get; set; }
    public DateTime? EndsAtUtc { get; set; }
    public bool IsActive { get; set; }
    public bool IsCurrent { get; set; }
    public string? Reason { get; set; }
}

public sealed class AdminEffectiveAccessDto
{
    public Guid UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public bool EmailConfirmed { get; set; }
    public bool AuthenticatedPublicAccess { get; set; }
    public IReadOnlyList<string> DirectRoles { get; set; } = Array.Empty<string>();
    public IReadOnlyList<string> EffectiveRoles { get; set; } = Array.Empty<string>();
    public IReadOnlyList<AdminStaffPositionAssignmentDto> ActiveStaffPositions { get; set; } = Array.Empty<AdminStaffPositionAssignmentDto>();
    public IReadOnlyList<AdminEffectivePermissionDto> EffectivePermissions { get; set; } = Array.Empty<AdminEffectivePermissionDto>();
    public IReadOnlyList<string> Warnings { get; set; } = Array.Empty<string>();
}

public sealed class AdminEffectivePermissionDto
{
    public string PermissionCode { get; set; } = string.Empty;
    public string EntityName { get; set; } = string.Empty;
    public string Operation { get; set; } = string.Empty;
    public IReadOnlyList<AdminEffectiveAccessSourceDto> Sources { get; set; } = Array.Empty<AdminEffectiveAccessSourceDto>();
}

public sealed class AdminEffectiveAccessSourceDto
{
    public string Audience { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Scope { get; set; } = string.Empty;
    public string OwnerField { get; set; } = string.Empty;
    public string Via { get; set; } = string.Empty;
}

public sealed class AdminUserInvitationDto
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public DateTime? AcceptedAtUtc { get; set; }
    public bool IsExpired { get; set; }
    public bool CanResend { get; set; }
    public IReadOnlyList<string> Roles { get; set; } = Array.Empty<string>();
}

public sealed class AdminEmailConfirmationDto
{
    public Guid UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public bool EmailConfirmed { get; set; }
    public DateTime? LastSentAtUtc { get; set; }
    public DateTime? LastExpiresAtUtc { get; set; }
    public DateTime? LastCompletedAtUtc { get; set; }
    public bool HasPendingToken { get; set; }
    public bool CanSend { get; set; }
}

public sealed class AdminIdentityAuditLogDto
{
    public Guid Id { get; set; }
    public DateTime CreatedAtUtc { get; set; }
    public string Action { get; set; } = string.Empty;
    public Guid? ActorUserId { get; set; }
    public string ActorEmail { get; set; } = string.Empty;
    public Guid? TargetUserId { get; set; }
    public string TargetEmail { get; set; } = string.Empty;
    public string Details { get; set; } = string.Empty;
}

public sealed class CreateAdminUserRequest
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public bool MustChangePassword { get; set; } = true;
    public IReadOnlyList<string> Roles { get; set; } = Array.Empty<string>();
}

public sealed class CreateUserInvitationRequest
{
    public string Email { get; set; } = string.Empty;
    public IReadOnlyList<string> Roles { get; set; } = Array.Empty<string>();
}

public sealed class AcceptUserInvitationRequest
{
    public string Token { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public sealed class AssignUserRoleRequest
{
    public string RoleCode { get; set; } = string.Empty;
}

public sealed class AssignStaffPositionRequest
{
    public string StaffPositionCode { get; set; } = string.Empty;
    public string AssignmentKind { get; set; } = "Primary";
    public DateTime? StartsAtUtc { get; set; }
    public DateTime? EndsAtUtc { get; set; }
    public string Reason { get; set; } = string.Empty;
}

public sealed class CloseStaffPositionAssignmentRequest
{
    public DateTime? EndsAtUtc { get; set; }
    public string Reason { get; set; } = string.Empty;
}
