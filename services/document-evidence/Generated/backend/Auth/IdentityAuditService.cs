#nullable enable

using System.Security.Claims;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Auth;

public sealed class IdentityAuditService
{
    private readonly DocumentEvidenceOperationalModelDbContext _db;
    private readonly IHttpContextAccessor _httpContext;

    public IdentityAuditService(DocumentEvidenceOperationalModelDbContext db, IHttpContextAccessor httpContext)
    {
        _db = db;
        _httpContext = httpContext;
    }

    public async Task RecordAsync(string action, Guid? targetUserId, string targetEmail, string details, CancellationToken ct)
    {
        var user = _httpContext.HttpContext?.User;
        var userId = ReadUserId(user);
        var email = user?.FindFirstValue(ClaimTypes.Email) ?? string.Empty;
        _db.IdentityAuditLogs.Add(new IdentityAuditLog
        {
            Id = Guid.NewGuid(),
            CreatedAtUtc = DateTime.UtcNow,
            Action = Clip(action, 120),
            ActorUserId = userId,
            ActorEmail = Clip(email, 320),
            TargetUserId = targetUserId,
            TargetEmail = Clip(targetEmail, 320),
            Details = Clip(details, 1000),
        });
        await _db.SaveChangesAsync(ct);
    }

    public async Task<IReadOnlyList<AdminIdentityAuditLogDto>> ListAsync(int take, CancellationToken ct)
    {
        var limit = Math.Clamp(take, 1, 500);
        return await _db.IdentityAuditLogs
            .OrderByDescending(x => x.CreatedAtUtc)
            .Take(limit)
            .Select(x => new AdminIdentityAuditLogDto
            {
                Id = x.Id,
                CreatedAtUtc = x.CreatedAtUtc,
                Action = x.Action,
                ActorUserId = x.ActorUserId,
                ActorEmail = x.ActorEmail,
                TargetUserId = x.TargetUserId,
                TargetEmail = x.TargetEmail,
                Details = x.Details,
            })
            .ToArrayAsync(ct);
    }

    private static Guid? ReadUserId(ClaimsPrincipal? user)
    {
        return user is not null && Guid.TryParse(user.FindFirstValue(ClaimTypes.NameIdentifier), out var id) ? id : null;
    }

    private static string Clip(string value, int maxLength)
    {
        return value.Length <= maxLength ? value : value[..maxLength];
    }
}
