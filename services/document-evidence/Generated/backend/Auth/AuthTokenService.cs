#nullable enable

using System.Security.Claims;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Auth;

public sealed class AuthTokenService
{
    private readonly DocumentEvidenceOperationalModelDbContext _db;
    private readonly IdentityAuditService _audit;
    private readonly IConfiguration _configuration;

    public AuthTokenService(DocumentEvidenceOperationalModelDbContext db, IdentityAuditService audit, IConfiguration configuration)
    {
        _db = db;
        _audit = audit;
        _configuration = configuration;
    }

    public async Task<AuthResponse> CreateResponseAsync(AppUser user, CancellationToken ct)
    {
        var accessToken = AuthCodeDigest.NewCode(64);
        var refreshToken = AuthCodeDigest.NewCode(64);
        var now = DateTime.UtcNow;
        _db.AppUserSessions.Add(new AppUserSession
        {
            Id = Guid.NewGuid(),
            AppUserId = user.Id,
            AccessTokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.AccessPurpose, accessToken),
            RefreshTokenHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.RefreshPurpose, refreshToken),
            AccessTokenExpiresAtUtc = now.AddHours(1),
            RefreshTokenExpiresAtUtc = now.AddDays(7),
            CreatedAtUtc = now,
        });
        await _db.SaveChangesAsync(ct);
        return new AuthResponse
        {
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAtUtc = now.AddHours(1),
            User = await BuildUserDtoAsync(user, ct),
        };
    }

    public async Task<ClaimsPrincipal?> AuthenticateAccessTokenAsync(string token, CancellationToken ct)
    {
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.AccessPurpose, token);
        var session = await _db.AppUserSessions.SingleOrDefaultAsync(x => x.AccessTokenHash == hash, ct);
        if (session is null || session.RevokedAtUtc is not null || session.AccessTokenExpiresAtUtc <= DateTime.UtcNow)
        {
            return null;
        }
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == session.AppUserId && x.IsActive, ct);
        return user is null ? null : await CreatePrincipalAsync(user, ct);
    }

    public async Task<AuthResponse?> RefreshAsync(string refreshToken, CancellationToken ct)
    {
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.RefreshPurpose, refreshToken);
        var session = await _db.AppUserSessions.SingleOrDefaultAsync(x => x.RefreshTokenHash == hash, ct);
        if (session is null || session.RevokedAtUtc is not null || session.RefreshTokenExpiresAtUtc <= DateTime.UtcNow)
        {
            return null;
        }
        var user = await _db.AppUsers.SingleOrDefaultAsync(x => x.Id == session.AppUserId && x.IsActive, ct);
        if (user is null)
        {
            return null;
        }
        session.RevokedAtUtc = DateTime.UtcNow;
        return await CreateResponseAsync(user, ct);
    }

    public async Task RevokeAccessTokenAsync(string token, CancellationToken ct)
    {
        var hash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.AccessPurpose, token);
        var session = await _db.AppUserSessions.SingleOrDefaultAsync(x => x.AccessTokenHash == hash, ct);
        if (session is not null && session.RevokedAtUtc is null)
        {
            session.RevokedAtUtc = DateTime.UtcNow;
            await _db.SaveChangesAsync(ct);
            await _audit.RecordAsync("Identity.Session.Logout", session.AppUserId, string.Empty, "sessionId=" + session.Id, ct);
        }
    }

    public async Task<IReadOnlyList<AuthSessionDto>> ListSessionsAsync(
        ClaimsPrincipal principal,
        string? currentAccessToken,
        CancellationToken ct)
    {
        if (!TryReadUserId(principal, out var userId))
        {
            return Array.Empty<AuthSessionDto>();
        }
        var currentHash = string.IsNullOrWhiteSpace(currentAccessToken)
            ? null
            : AuthCodeDigest.Create(_configuration, AuthCodeDigest.AccessPurpose, currentAccessToken);
        return await _db.AppUserSessions
            .Where(x => x.AppUserId == userId)
            .OrderByDescending(x => x.CreatedAtUtc)
            .Select(x => new AuthSessionDto
            {
                Id = x.Id,
                CreatedAtUtc = x.CreatedAtUtc,
                AccessTokenExpiresAtUtc = x.AccessTokenExpiresAtUtc,
                RefreshTokenExpiresAtUtc = x.RefreshTokenExpiresAtUtc,
                RevokedAtUtc = x.RevokedAtUtc,
                IsCurrent = currentHash != null && x.AccessTokenHash == currentHash,
            })
            .ToArrayAsync(ct);
    }

    public async Task<bool> RevokeSessionAsync(ClaimsPrincipal principal, Guid sessionId, CancellationToken ct)
    {
        if (!TryReadUserId(principal, out var userId))
        {
            return false;
        }
        var session = await _db.AppUserSessions.SingleOrDefaultAsync(x => x.Id == sessionId && x.AppUserId == userId, ct);
        if (session is null)
        {
            return false;
        }
        if (session.RevokedAtUtc is null)
        {
            session.RevokedAtUtc = DateTime.UtcNow;
            await _db.SaveChangesAsync(ct);
            await _audit.RecordAsync("Identity.Session.Revoke", userId, string.Empty, "sessionId=" + session.Id, ct);
        }
        return true;
    }

    public async Task<int> RevokeOtherSessionsAsync(
        ClaimsPrincipal principal,
        string? currentAccessToken,
        CancellationToken ct)
    {
        if (!TryReadUserId(principal, out var userId) || string.IsNullOrWhiteSpace(currentAccessToken))
        {
            return 0;
        }
        var currentHash = AuthCodeDigest.Create(_configuration, AuthCodeDigest.AccessPurpose, currentAccessToken);
        var now = DateTime.UtcNow;
        var sessions = await _db.AppUserSessions
            .Where(x => x.AppUserId == userId && x.RevokedAtUtc == null && x.AccessTokenHash != currentHash)
            .ToListAsync(ct);
        foreach (var session in sessions)
        {
            session.RevokedAtUtc = now;
        }
        await _db.SaveChangesAsync(ct);
        await _audit.RecordAsync("Identity.Session.RevokeOther", userId, string.Empty, "count=" + sessions.Count, ct);
        return sessions.Count;
    }

    public AuthUserDto UserFromPrincipal(ClaimsPrincipal principal)
    {
        var id = Guid.TryParse(principal.FindFirstValue(ClaimTypes.NameIdentifier), out var userId) ? userId : Guid.Empty;
        return new AuthUserDto
        {
            Id = id,
            Email = principal.FindFirstValue(ClaimTypes.Email) ?? string.Empty,
            UserName = principal.Identity?.Name ?? string.Empty,
            MustChangePassword = principal.HasClaim("mustChangePassword", "true"),
            EmailConfirmed = principal.HasClaim("emailConfirmed", "true"),
            Roles = principal.FindAll(ClaimTypes.Role).Select(x => x.Value).Distinct().OrderBy(x => x).ToArray(),
            Permissions = principal.FindAll("permission").Select(x => x.Value).Distinct().OrderBy(x => x).ToArray(),
        };
    }

    private async Task<ClaimsPrincipal> CreatePrincipalAsync(AppUser user, CancellationToken ct)
    {
        var dto = await BuildUserDtoAsync(user, ct);
        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user.Id.ToString("D")),
            new("sub", user.Id.ToString("D")),
            new(ClaimTypes.Email, user.Email),
            new(ClaimTypes.Name, user.UserName),
            new("mustChangePassword", user.MustChangePassword ? "true" : "false"),
            new("emailConfirmed", user.EmailConfirmed ? "true" : "false"),
        };
        claims.AddRange(dto.Roles.Select(role => new Claim(ClaimTypes.Role, role)));
        claims.AddRange(dto.Permissions.Select(permission => new Claim("permission", permission)));
        return new ClaimsPrincipal(new ClaimsIdentity(claims, "AppForgeGenerated"));
    }

    private async Task<AuthUserDto> BuildUserDtoAsync(AppUser user, CancellationToken ct)
    {
        var roles = await UserRoleQuery(user.Id).ToArrayAsync(ct);
        var roleIds = await _db.AppUserRoles.Where(x => x.AppUserId == user.Id).Select(x => x.RoleId).ToArrayAsync(ct);
        var permissions = await _db.RolePermissions
            .Where(x => roleIds.Contains(x.RoleId))
            .Join(_db.Permissions, x => x.PermissionId, x => x.Id, (_, permission) => permission.Code)
            .Distinct()
            .OrderBy(x => x)
            .ToArrayAsync(ct);
        return new AuthUserDto
        {
            Id = user.Id,
            Email = user.Email,
            UserName = user.UserName,
            MustChangePassword = user.MustChangePassword,
            EmailConfirmed = user.EmailConfirmed,
            Roles = roles,
            Permissions = permissions,
        };
    }

    private IQueryable<string> UserRoleQuery(Guid userId)
    {
        return _db.AppUserRoles
            .Where(x => x.AppUserId == userId)
            .Join(_db.Roles, x => x.RoleId, x => x.Id, (_, role) => role.Code)
            .Distinct()
            .OrderBy(x => x);
    }

    private static bool TryReadUserId(ClaimsPrincipal principal, out Guid userId)
    {
        return Guid.TryParse(principal.FindFirstValue(ClaimTypes.NameIdentifier), out userId);
    }

    public static string? ReadBearerToken(HttpRequest request)
    {
        var header = request.Headers["Authorization"].FirstOrDefault();
        return header?.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase) == true
            ? header["Bearer ".Length..].Trim()
            : null;
    }
}
