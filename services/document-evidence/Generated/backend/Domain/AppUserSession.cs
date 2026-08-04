#nullable enable

namespace LogicLens.DocumentEvidence.Generated;

public sealed class AppUserSession
{
    public Guid Id { get; set; }
    public Guid AppUserId { get; set; }
    public string AccessTokenHash { get; set; } = string.Empty;
    public string RefreshTokenHash { get; set; } = string.Empty;
    public DateTime AccessTokenExpiresAtUtc { get; set; }
    public DateTime RefreshTokenExpiresAtUtc { get; set; }
    public DateTime? RevokedAtUtc { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class AuthLoginAttempt
{
    public Guid Id { get; set; }
    public string LoginHash { get; set; } = string.Empty;
    public string IpHash { get; set; } = string.Empty;
    public bool Succeeded { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class PasswordResetToken
{
    public Guid Id { get; set; }
    public Guid AppUserId { get; set; }
    public string TokenHash { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public DateTime? UsedAtUtc { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class AccountRecoveryAttempt
{
    public Guid Id { get; set; }
    public string EmailHash { get; set; } = string.Empty;
    public string IpHash { get; set; } = string.Empty;
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class PublicRegistrationAttempt
{
    public Guid Id { get; set; }
    public string EmailHash { get; set; } = string.Empty;
    public string IpHash { get; set; } = string.Empty;
    public bool Succeeded { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class UserInvitation
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string TokenHash { get; set; } = string.Empty;
    public string RoleCodes { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public DateTime? AcceptedAtUtc { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class EmailConfirmationToken
{
    public Guid Id { get; set; }
    public Guid AppUserId { get; set; }
    public string TokenHash { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public DateTime? UsedAtUtc { get; set; }
    public DateTime CreatedAtUtc { get; set; }
}

public sealed class IdentityAuditLog
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
