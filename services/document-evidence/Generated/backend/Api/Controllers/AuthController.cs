#nullable enable

using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Auth;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LogicLens.DocumentEvidence.Generated.Api.Controllers;

[ApiController]
[Route("api/auth")]
public sealed class AuthController : ControllerBase
{
    private readonly AuthLoginService _login;
    private readonly AuthTokenService _tokens;
    private readonly Microsoft.Extensions.Configuration.IConfiguration _configuration;

    public AuthController(
        AuthLoginService login,
        AuthTokenService tokens,
        Microsoft.Extensions.Configuration.IConfiguration configuration)
    {
        _login = login;
        _tokens = tokens;
        _configuration = configuration;
    }

    [HttpGet("features")]
    public ActionResult<AppAuthFeatureDiagnosticsDto> Features()
    {
        return Ok(AuthFeatureOptionsExtensions.GetDiagnostics(_configuration));
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register(RegisterRequest request, CancellationToken ct)
    {
        if (!AuthFeatureOptionsExtensions.ReadOptions(_configuration).PublicRegistrationEnabled)
        {
            return NotFound();
        }
        return await _login.RegisterAsync(request, ct) ? NoContent() : BadRequest(new { error = "Registration was not completed." });
    }

    [HttpPost("login")]
    public async Task<ActionResult<AuthResponse>> Login(LoginRequest request, CancellationToken ct)
    {
        var response = await _login.LoginAsync(request, ct);
        return response is null ? Unauthorized(new { error = "Invalid login or password." }) : Ok(response);
    }

    [HttpPost("account-recovery/start")]
    [HttpPost("/api/account/forgot-password")]
    public async Task<IActionResult> StartAccountRecovery(AccountRecoveryRequest request, CancellationToken ct)
    {
        await _login.StartAccountRecoveryAsync(request, ct);
        return NoContent();
    }

    [HttpPost("account-recovery/complete")]
    [HttpPost("/api/account/reset-password")]
    public async Task<IActionResult> CompleteAccountRecovery(CompleteAccountRecoveryRequest request, CancellationToken ct)
    {
        return await _login.CompleteAccountRecoveryAsync(request, ct) ? NoContent() : BadRequest();
    }

    [HttpPost("email-confirmation/complete")]
    public async Task<IActionResult> CompleteEmailConfirmation(ConfirmEmailRequest request, CancellationToken ct)
    {
        return await _login.ConfirmEmailAsync(request, ct) ? NoContent() : BadRequest();
    }

    [HttpPost("invitations/accept")]
    public async Task<IActionResult> AcceptInvitation(AcceptUserInvitationRequest request, CancellationToken ct)
    {
        return await _login.AcceptInvitationAsync(request, ct) ? NoContent() : BadRequest();
    }

    [Authorize]
    [HttpGet("me")]
    public ActionResult<AuthUserDto> Me()
    {
        return Ok(_tokens.UserFromPrincipal(User));
    }

    [Authorize]
    [HttpGet("sessions")]
    public async Task<IReadOnlyList<AuthSessionDto>> Sessions(CancellationToken ct)
    {
        return await _tokens.ListSessionsAsync(User, AuthTokenService.ReadBearerToken(Request), ct);
    }

    [Authorize]
    [HttpPost("sessions/{sessionId:guid}/revoke")]
    public async Task<IActionResult> RevokeSession(Guid sessionId, CancellationToken ct)
    {
        return await _tokens.RevokeSessionAsync(User, sessionId, ct) ? NoContent() : NotFound();
    }

    [Authorize]
    [HttpPost("sessions/revoke-other")]
    public async Task<IActionResult> RevokeOtherSessions(CancellationToken ct)
    {
        var revoked = await _tokens.RevokeOtherSessionsAsync(User, AuthTokenService.ReadBearerToken(Request), ct);
        return Ok(new { revoked });
    }

    [Authorize]
    [HttpPost("logout")]
    public async Task<IActionResult> Logout(CancellationToken ct)
    {
        var token = AuthTokenService.ReadBearerToken(Request);
        if (!string.IsNullOrWhiteSpace(token))
        {
            await _tokens.RevokeAccessTokenAsync(token, ct);
        }
        return NoContent();
    }

    [HttpPost("refresh")]
    public async Task<ActionResult<AuthResponse>> Refresh(RefreshTokenRequest request, CancellationToken ct)
    {
        var response = await _tokens.RefreshAsync(request.RefreshToken, ct);
        return response is null ? Unauthorized(new { error = "Invalid refresh token." }) : Ok(response);
    }

    [Authorize]
    [HttpPost("change-password")]
    public async Task<IActionResult> ChangePassword(ChangePasswordRequest request, CancellationToken ct)
    {
        var ok = await _login.ChangePasswordAsync(User, request, ct);
        return ok ? NoContent() : BadRequest(new { error = "Password was not changed." });
    }
}
