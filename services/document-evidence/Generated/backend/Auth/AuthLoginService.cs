#nullable enable

using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Auth;

public sealed class AuthLoginService
{
    private readonly DocumentEvidenceOperationalModelDbContext _db;
    private readonly AuthTokenService _tokens;
    private readonly IAppEmailSender _email;
    private readonly IConfiguration _configuration;
    private readonly IHttpContextAccessor _httpContext;
    private readonly IdentityAuditService _audit;
    private readonly PasswordHasher<AppUser> _hasher = new();

    public AuthLoginService(
        DocumentEvidenceOperationalModelDbContext db,
        AuthTokenService tokens,
        IAppEmailSender email,
        IConfiguration configuration,
        IHttpContextAccessor httpContext,
        IdentityAuditService audit)
    {
        _db = db;
        _tokens = tokens;
        _email = email;
        _configuration = configuration;
        _httpContext = httpContext;
        _audit = audit;
    }

    public async Task<AuthResponse?> LoginAsync(LoginRequest request, CancellationToken ct)
    {
        var login = request.Login.Trim();
        var loginHash = HashCode(login.ToUpperInvariant());
        var ipHash = HashCode(ReadClientAddress());
        if (await IsLoginRateLimitedAsync(loginHash, ipHash, ct))
        {
            return null;
        }

        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Email == login || x.UserName == login, ct);
        if (user is null || !user.IsActive)
        {
            await RecordLoginAttemptAsync(loginHash, ipHash, succeeded: false, ct);
            return null;
        }
        var result = _hasher.VerifyHashedPassword(user, user.PasswordHash, request.Password);
        if (result == PasswordVerificationResult.Failed)
        {
            await RecordLoginAttemptAsync(loginHash, ipHash, succeeded: false, ct);
            return null;
        }
        if (AuthFeatureOptionsExtensions.ReadOptions(_configuration).RequireConfirmedEmailForLogin && !user.EmailConfirmed)
        {
            await RecordLoginAttemptAsync(loginHash, ipHash, succeeded: false, ct);
            await _audit.RecordAsync("Identity.Login.BlockedUnconfirmedEmail", user.Id, user.Email, string.Empty, ct);
            return null;
        }
        if (result == PasswordVerificationResult.SuccessRehashNeeded)
        {
            user.PasswordHash = _hasher.HashPassword(user, request.Password);
            await _db.SaveChangesAsync(ct);
        }
        await RecordLoginAttemptAsync(loginHash, ipHash, succeeded: true, ct);
        return await _tokens.CreateResponseAsync(user, ct);
    }

    public async Task<bool> RegisterAsync(RegisterRequest request, CancellationToken ct)
    {
        var email = request.Email.Trim();
        var normalizedEmail = email.ToUpperInvariant();
        var emailHash = HashCode(normalizedEmail);
        var ipHash = HashCode(ReadClientAddress());
        var abuse = AuthAbuseProtectionOptionsExtensions.ReadOptions(_configuration);
        if (abuse.RegistrationAbuseProtectionEnabled && await IsRegistrationRateLimitedAsync(emailHash, ipHash, abuse, ct))
        {
            await RecordRegistrationAttemptAsync(emailHash, ipHash, succeeded: false, ct);
            await _audit.RecordAsync("Identity.Registration.RateLimited", null, email, string.Empty, ct);
            return false;
        }
        if (email.Length == 0 || !email.Contains('@') || request.Password.Length < 8)
        {
            await RecordRegistrationAttemptAsync(emailHash, ipHash, succeeded: false, ct);
            return false;
        }
        if (await _db.AppUsers.AnyAsync(x => x.Email == email, ct))
        {
            await RecordRegistrationAttemptAsync(emailHash, ipHash, succeeded: false, ct);
            return false;
        }
        var now = DateTime.UtcNow;
        var user = new AppUser
        {
            Id = Guid.NewGuid(),
            Email = email,
            UserName = email,
            EmailConfirmed = false,
            IsActive = true,
            MustChangePassword = false,
            CreatedAtUtc = now,
            UpdatedAtUtc = now,
        };
        user.PasswordHash = _hasher.HashPassword(user, request.Password);
        var confirmationCode = AuthCodeDigest.NewCode(32);
        var confirmationExpiresAtUtc = now.AddHours(24);
        _db.AppUsers.Add(user);
        _db.EmailConfirmationTokens.Add(new EmailConfirmationToken
        {
            Id = Guid.NewGuid(),
            AppUserId = user.Id,
            TokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.ConfirmationPurpose, confirmationCode),
            ExpiresAtUtc = confirmationExpiresAtUtc,
            CreatedAtUtc = now,
        });
        await RecordRegistrationAttemptAsync(emailHash, ipHash, succeeded: true, ct);
        await _db.SaveChangesAsync(ct);
        await _email.SendAsync(AppEmailTemplates.EmailConfirmation(
            AppEmailTemplates.ReadOptions(_configuration),
            user.Email,
            confirmationCode,
            confirmationExpiresAtUtc), ct);
        await _audit.RecordAsync("Identity.Registration.Self", user.Id, user.Email, string.Empty, ct);
        await _audit.RecordAsync("Identity.Registration.EmailConfirmation.Send", user.Id, user.Email, "expiresAtUtc=" + confirmationExpiresAtUtc.ToString("O"), ct);
        return true;
    }

    public async Task StartAccountRecoveryAsync(AccountRecoveryRequest request, CancellationToken ct)
    {
        var email = request.Email.Trim().ToUpperInvariant();
        var emailHash = HashCode(email);
        var ipHash = HashCode(ReadClientAddress());
        if (await IsRecoveryRateLimitedAsync(emailHash, ipHash, ct))
        {
            return;
        }
        await RecordRecoveryAttemptAsync(emailHash, ipHash, ct);

        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Email.ToUpper() == email && x.IsActive, ct);
        if (user is null)
        {
            return;
        }
        var code = AuthCodeDigest.NewCode(32);
        var now = DateTime.UtcNow;
        var expiresAtUtc = now.AddMinutes(30);
        _db.PasswordResetTokens.Add(new PasswordResetToken
        {
            Id = Guid.NewGuid(),
            AppUserId = user.Id,
            TokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.RecoveryPurpose, code),
            ExpiresAtUtc = expiresAtUtc,
            CreatedAtUtc = now,
        });
        await _db.SaveChangesAsync(ct);
        await _email.SendAsync(AppEmailTemplates.AccountRecovery(
            AppEmailTemplates.ReadOptions(_configuration),
            user.Email,
            code,
            expiresAtUtc), ct);
    }

    public async Task<bool> CompleteAccountRecoveryAsync(CompleteAccountRecoveryRequest request, CancellationToken ct)
    {
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.RecoveryPurpose, request.Code);
        var now = DateTime.UtcNow;
        var entry = await _db.PasswordResetTokens.SingleOrDefaultAsync(x => x.TokenHash == hash, ct);
        if (entry is null || entry.UsedAtUtc is not null || entry.ExpiresAtUtc <= now)
        {
            return false;
        }
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == entry.AppUserId && x.IsActive, ct);
        if (user is null)
        {
            return false;
        }
        user.PasswordHash = _hasher.HashPassword(user, request.NewPassword);
        user.MustChangePassword = false;
        user.UpdatedAtUtc = now;
        entry.UsedAtUtc = now;
        var sessions = await _db.AppUserSessions.Where(x => x.AppUserId == user.Id && x.RevokedAtUtc == null).ToListAsync(ct);
        foreach (var session in sessions)
        {
            session.RevokedAtUtc = now;
        }
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.AccountRecovery.Complete", user.Id, user.Email, "revokedSessions=" + sessions.Count, ct);
        return true;
    }

    public async Task<bool> ConfirmEmailAsync(ConfirmEmailRequest request, CancellationToken ct)
    {
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.ConfirmationPurpose, request.Code);
        var now = DateTime.UtcNow;
        var entry = await _db.EmailConfirmationTokens.SingleOrDefaultAsync(x => x.TokenHash == hash, ct);
        if (entry is null || entry.UsedAtUtc is not null || entry.ExpiresAtUtc <= now)
        {
            return false;
        }
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == entry.AppUserId && x.IsActive, ct);
        if (user is null)
        {
            return false;
        }
        user.EmailConfirmed = true;
        user.UpdatedAtUtc = now;
        entry.UsedAtUtc = now;
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.EmailConfirmation.Complete", user.Id, user.Email, string.Empty, ct);
        return true;
    }

    public async Task<bool> AcceptInvitationAsync(AcceptUserInvitationRequest request, CancellationToken ct)
    {
        if (request.Password.Length < 8)
        {
            return false;
        }
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.InvitationPurpose, request.Token);
        var now = DateTime.UtcNow;
        var invitation = await _db.UserInvitations.SingleOrDefaultAsync(x => x.TokenHash == hash, ct);
        if (invitation is null || invitation.AcceptedAtUtc is not null || invitation.ExpiresAtUtc <= now)
        {
            return false;
        }
        if (await _db.AppUsers.AnyAsync(x => x.Email == invitation.Email, ct))
        {
            return false;
        }
        var user = new AppUser
        {
            Id = Guid.NewGuid(),
            Email = invitation.Email,
            UserName = invitation.Email,
            EmailConfirmed = true,
            IsActive = true,
            MustChangePassword = false,
            CreatedAtUtc = now,
            UpdatedAtUtc = now,
        };
        user.PasswordHash = _hasher.HashPassword(user, request.Password);
        _db.AppUsers.Add(user);
        foreach (var roleCode in invitation.RoleCodes.Split('|', StringSplitOptions.RemoveEmptyEntries))
        {
            await AssignRoleAsync(user.Id, roleCode, ct);
        }
        invitation.AcceptedAtUtc = now;
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.Invitation.Accept", user.Id, user.Email, "roles=" + invitation.RoleCodes, ct);
        return true;
    }

    public async Task<bool> ChangePasswordAsync(ClaimsPrincipal principal, ChangePasswordRequest request, CancellationToken ct)
    {
        var idValue = principal.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(idValue, out var userId))
        {
            return false;
        }
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == userId, ct);
        if (user is null || !user.IsActive)
        {
            return false;
        }
        var result = _hasher.VerifyHashedPassword(user, user.PasswordHash, request.CurrentPassword);
        if (result == PasswordVerificationResult.Failed)
        {
            return false;
        }
        user.PasswordHash = _hasher.HashPassword(user, request.NewPassword);
        user.MustChangePassword = false;
        user.UpdatedAtUtc = DateTime.UtcNow;
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.Password.Change", user.Id, user.Email, string.Empty, ct);
        return true;
    }

    private async Task<bool> IsLoginRateLimitedAsync(string loginHash, string ipHash, CancellationToken ct)
    {
        var windowStart = DateTime.UtcNow.AddMinutes(-15);
        var loginFailures = await _db.AuthLoginAttempts.CountAsync(x => x.LoginHash == loginHash && !x.Succeeded && x.CreatedAtUtc >= windowStart, ct);
        var ipFailures = await _db.AuthLoginAttempts.CountAsync(x => x.IpHash == ipHash && !x.Succeeded && x.CreatedAtUtc >= windowStart, ct);
        return loginFailures >= 5 || ipFailures >= 20;
    }

    private async Task RecordLoginAttemptAsync(string loginHash, string ipHash, bool succeeded, CancellationToken ct)
    {
        _db.AuthLoginAttempts.Add(new AuthLoginAttempt
        {
            Id = Guid.NewGuid(),
            LoginHash = loginHash,
            IpHash = ipHash,
            Succeeded = succeeded,
            CreatedAtUtc = DateTime.UtcNow,
        });
        await _db.SaveChangesAsync(ct);
    }

    private async Task<bool> IsRecoveryRateLimitedAsync(string emailHash, string ipHash, CancellationToken ct)
    {
        var windowStart = DateTime.UtcNow.AddHours(-1);
        var emailCount = await _db.AccountRecoveryAttempts.CountAsync(x => x.EmailHash == emailHash && x.CreatedAtUtc >= windowStart, ct);
        var ipCount = await _db.AccountRecoveryAttempts.CountAsync(x => x.IpHash == ipHash && x.CreatedAtUtc >= windowStart, ct);
        return emailCount >= 3 || ipCount >= 10;
    }

    private async Task RecordRecoveryAttemptAsync(string emailHash, string ipHash, CancellationToken ct)
    {
        _db.AccountRecoveryAttempts.Add(new AccountRecoveryAttempt
        {
            Id = Guid.NewGuid(),
            EmailHash = emailHash,
            IpHash = ipHash,
            CreatedAtUtc = DateTime.UtcNow,
        });
        await _db.SaveChangesAsync(ct);
    }

    private async Task<bool> IsRegistrationRateLimitedAsync(
        string emailHash,
        string ipHash,
        AppAuthAbuseProtectionOptions options,
        CancellationToken ct)
    {
        var windowStart = DateTime.UtcNow.AddHours(-1);
        var emailCount = await _db.PublicRegistrationAttempts.CountAsync(x => x.EmailHash == emailHash && x.CreatedAtUtc >= windowStart, ct);
        var ipCount = await _db.PublicRegistrationAttempts.CountAsync(x => x.IpHash == ipHash && x.CreatedAtUtc >= windowStart, ct);
        return emailCount >= options.RegistrationEmailLimitPerHour || ipCount >= options.RegistrationIpLimitPerHour;
    }

    private async Task RecordRegistrationAttemptAsync(string emailHash, string ipHash, bool succeeded, CancellationToken ct)
    {
        _db.PublicRegistrationAttempts.Add(new PublicRegistrationAttempt
        {
            Id = Guid.NewGuid(),
            EmailHash = emailHash,
            IpHash = ipHash,
            Succeeded = succeeded,
            CreatedAtUtc = DateTime.UtcNow,
        });
        await _db.SaveChangesAsync(ct);
    }

    private string ReadClientAddress()
    {
        return _httpContext.HttpContext?.Connection.RemoteIpAddress?.ToString() ?? "unknown";
    }

    private async Task AssignRoleAsync(Guid userId, string roleCode, CancellationToken ct)
    {
        var role = await _db.Roles.SingleOrDefaultAsync(x => x.Code == roleCode.Trim(), ct);
        if (role is null)
        {
            return;
        }
        var hasRole = await _db.AppUserRoles.AnyAsync(x => x.AppUserId == userId && x.RoleId == role.Id, ct);
        if (!hasRole)
        {
            _db.AppUserRoles.Add(new AppUserRole { Id = Guid.NewGuid(), AppUserId = userId, RoleId = role.Id });
        }
    }

    private static string HashCode(string code)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(code));
        return Convert.ToHexString(bytes);
    }
}
