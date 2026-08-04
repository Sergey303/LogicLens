#nullable enable

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class LoginRequest
{
    public string Login { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public sealed class RegisterRequest
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public sealed class RefreshTokenRequest
{
    public string RefreshToken { get; set; } = string.Empty;
}

public sealed class ChangePasswordRequest
{
    public string CurrentPassword { get; set; } = string.Empty;
    public string NewPassword { get; set; } = string.Empty;
}

public sealed class AccountRecoveryRequest
{
    public string Email { get; set; } = string.Empty;
}

public sealed class CompleteAccountRecoveryRequest
{
    public string Code { get; set; } = string.Empty;
    public string NewPassword { get; set; } = string.Empty;
}

public sealed class ConfirmEmailRequest
{
    public string Code { get; set; } = string.Empty;
}

public sealed class AuthResponse
{
    public string AccessToken { get; set; } = string.Empty;
    public string RefreshToken { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public AuthUserDto User { get; set; } = new();
}

public sealed class AuthUserDto
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public bool MustChangePassword { get; set; }
    public bool EmailConfirmed { get; set; }
    public IReadOnlyList<string> Roles { get; set; } = Array.Empty<string>();
    public IReadOnlyList<string> Permissions { get; set; } = Array.Empty<string>();
}

public sealed class AuthSessionDto
{
    public Guid Id { get; set; }
    public DateTime CreatedAtUtc { get; set; }
    public DateTime AccessTokenExpiresAtUtc { get; set; }
    public DateTime RefreshTokenExpiresAtUtc { get; set; }
    public DateTime? RevokedAtUtc { get; set; }
    public bool IsCurrent { get; set; }
}

public sealed class AppAuthFeatureOptions
{
    public bool PublicRegistrationEnabled { get; set; } = false;
    public bool RequireConfirmedEmailForLogin { get; set; } = true;
}

public sealed class AppAuthFeatureDiagnosticsDto
{
    public bool PublicRegistrationEnabled { get; set; }
    public bool PublicRegistrationEndpointAvailable { get; set; }
    public bool RequireConfirmedEmailForLogin { get; set; }
    public IReadOnlyList<string> Warnings { get; set; } = Array.Empty<string>();
}

public static class AuthFeatureOptionsExtensions
{
    public static AppAuthFeatureOptions ReadOptions(IConfiguration configuration)
    {
        var options = new AppAuthFeatureOptions();
        configuration.GetSection("AppForge:Auth").Bind(options);
        return options;
    }

    public static AppAuthFeatureDiagnosticsDto GetDiagnostics(IConfiguration configuration)
    {
        var options = ReadOptions(configuration);
        var warnings = new List<string>();
        if (!options.PublicRegistrationEnabled)
        {
            warnings.Add("Public registration endpoint is generated, but disabled by AppForge:Auth:PublicRegistrationEnabled.");
        }
        if (!options.RequireConfirmedEmailForLogin)
        {
            warnings.Add("Email confirmation is not required for login. Enable AppForge:Auth:RequireConfirmedEmailForLogin for public registration safety.");
        }
        return new AppAuthFeatureDiagnosticsDto
        {
            PublicRegistrationEnabled = options.PublicRegistrationEnabled,
            PublicRegistrationEndpointAvailable = true,
            RequireConfirmedEmailForLogin = options.RequireConfirmedEmailForLogin,
            Warnings = warnings.ToArray(),
        };
    }
}

public sealed class AppEmailMessage
{
    public string To { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Body { get; set; } = string.Empty;
}

public interface IAppEmailSender
{
    Task SendAsync(AppEmailMessage message, CancellationToken ct = default);
}

public sealed class DisabledEmailSender : IAppEmailSender
{
    public Task SendAsync(AppEmailMessage message, CancellationToken ct = default) => Task.CompletedTask;
}

public sealed class LogEmailSender : IAppEmailSender
{
    private readonly ILogger<LogEmailSender> _logger;

    public LogEmailSender(ILogger<LogEmailSender> logger)
    {
        _logger = logger;
    }

    public Task SendAsync(AppEmailMessage message, CancellationToken ct = default)
    {
        _logger.LogInformation("Generated email to {To}: {Subject}", message.To, message.Subject);
        return Task.CompletedTask;
    }
}

public sealed class AppEmailTemplateOptions
{
    public string ProductName { get; set; } = "AppForge";
    public string PublicBaseUrl { get; set; } = string.Empty;
    public string AccountRecoveryPath { get; set; } = "/reset-password";
    public string InvitationAcceptPath { get; set; } = "/accept-invite";
    public string EmailConfirmationPath { get; set; } = "/confirm-email";
    public string SupportEmail { get; set; } = string.Empty;
}

public static class AppEmailTemplates
{
    public static AppEmailTemplateOptions ReadOptions(IConfiguration configuration)
    {
        var options = new AppEmailTemplateOptions();
        configuration.GetSection("AppForge:Email:Templates").Bind(options);
        if (string.IsNullOrWhiteSpace(options.ProductName))
        {
            options.ProductName = "AppForge";
        }
        if (string.IsNullOrWhiteSpace(options.AccountRecoveryPath))
        {
            options.AccountRecoveryPath = "/reset-password";
        }
        if (string.IsNullOrWhiteSpace(options.InvitationAcceptPath))
        {
            options.InvitationAcceptPath = "/accept-invite";
        }
        if (string.IsNullOrWhiteSpace(options.EmailConfirmationPath))
        {
            options.EmailConfirmationPath = "/confirm-email";
        }
        return options;
    }

    public static AppEmailMessage AccountRecovery(
        AppEmailTemplateOptions options,
        string to,
        string code,
        DateTime expiresAtUtc)
    {
        var link = BuildActionLink(options, options.AccountRecoveryPath, "code", code);
        return new AppEmailMessage
        {
            To = to,
            Subject = $"{options.ProductName}: account recovery",
            Body = ComposeBody(
                options,
                "You requested password recovery.",
                $"Recovery code: {code}",
                $"Expires at UTC: {expiresAtUtc:O}",
                link),
        };
    }

    public static AppEmailMessage Invitation(
        AppEmailTemplateOptions options,
        string to,
        string token,
        DateTime expiresAtUtc,
        IReadOnlyList<string> roles)
    {
        var link = BuildActionLink(options, options.InvitationAcceptPath, "token", token);
        var roleText = roles.Count == 0 ? "Roles: none" : "Roles: " + string.Join(", ", roles);
        return new AppEmailMessage
        {
            To = to,
            Subject = $"{options.ProductName}: user invitation",
            Body = ComposeBody(
                options,
                $"You have been invited to {options.ProductName}.",
                roleText,
                $"Invitation token: {token}",
                $"Expires at UTC: {expiresAtUtc:O}",
                link),
        };
    }

    public static AppEmailMessage EmailConfirmation(
        AppEmailTemplateOptions options,
        string to,
        string code,
        DateTime expiresAtUtc)
    {
        var link = BuildActionLink(options, options.EmailConfirmationPath, "code", code);
        return new AppEmailMessage
        {
            To = to,
            Subject = $"{options.ProductName}: email confirmation",
            Body = ComposeBody(
                options,
                "Confirm this email address to finish account setup.",
                $"Confirmation code: {code}",
                $"Expires at UTC: {expiresAtUtc:O}",
                link),
        };
    }

    private static string ComposeBody(AppEmailTemplateOptions options, params string[] lines)
    {
        var bodyLines = new List<string> { options.ProductName, string.Empty };
        bodyLines.AddRange(lines.Where(x => !string.IsNullOrWhiteSpace(x)));
        if (!string.IsNullOrWhiteSpace(options.SupportEmail))
        {
            bodyLines.Add(string.Empty);
            bodyLines.Add($"Support: {options.SupportEmail}");
        }
        return string.Join(Environment.NewLine, bodyLines);
    }

    private static string BuildActionLink(AppEmailTemplateOptions options, string path, string parameterName, string value)
    {
        if (string.IsNullOrWhiteSpace(options.PublicBaseUrl))
        {
            return string.Empty;
        }
        var baseUrl = options.PublicBaseUrl.TrimEnd('/');
        var normalizedPath = path.StartsWith('/') ? path : "/" + path;
        var separator = normalizedPath.Contains('?') ? "&" : "?";
        return "Open link: " + baseUrl + normalizedPath + separator + parameterName + "=" + Uri.EscapeDataString(value);
    }
}

public sealed class SmtpEmailOptions
{
    public string Host { get; set; } = string.Empty;
    public int Port { get; set; } = 25;
    public string From { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public bool EnableSsl { get; set; } = true;
}

public sealed class AppEmailProviderDiagnosticsDto
{
    public string Mode { get; set; } = string.Empty;
    public bool IsProduction { get; set; }
    public bool EmailFeaturesEnabled { get; set; }
    public bool SmtpConfigured { get; set; }
    public bool HostConfigured { get; set; }
    public int Port { get; set; }
    public bool FromConfigured { get; set; }
    public bool UserNameConfigured { get; set; }
    public bool PasswordConfigured { get; set; }
    public bool EnableSsl { get; set; }
    public IReadOnlyList<string> Problems { get; set; } = Array.Empty<string>();
}

public sealed class SmtpEmailSender : IAppEmailSender
{
    private readonly IConfiguration _configuration;

    public SmtpEmailSender(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public async Task SendAsync(AppEmailMessage message, CancellationToken ct = default)
    {
        var options = EmailServiceCollectionExtensions.ReadSmtpOptions(_configuration);
        using var smtp = new System.Net.Mail.SmtpClient(options.Host, options.Port);
        smtp.EnableSsl = options.EnableSsl;
        if (!string.IsNullOrWhiteSpace(options.UserName))
        {
            smtp.Credentials = new System.Net.NetworkCredential(options.UserName, options.Password);
        }
        using var mail = new System.Net.Mail.MailMessage(options.From, message.To, message.Subject, message.Body);
        await smtp.SendMailAsync(mail, ct);
    }
}

public static class EmailServiceCollectionExtensions
{
    public static IServiceCollection AddAppForgeEmail(
        this IServiceCollection services,
        IConfiguration configuration,
        bool emailFeaturesEnabled,
        bool isProduction)
    {
        var mode = ReadConfiguredEmailMode(configuration, isProduction);
        var diagnostics = GetDiagnostics(configuration, emailFeaturesEnabled, isProduction);
        if (diagnostics.Problems.Count > 0)
        {
            throw new InvalidOperationException("Email configuration is invalid: " + string.Join("; ", diagnostics.Problems));
        }
        if (mode.Equals("Smtp", StringComparison.OrdinalIgnoreCase))
        {
            services.AddSingleton<IAppEmailSender, SmtpEmailSender>();
            return services;
        }
        if (mode.Equals("LogOnly", StringComparison.OrdinalIgnoreCase))
        {
            services.AddSingleton<IAppEmailSender, LogEmailSender>();
            return services;
        }
        services.AddSingleton<IAppEmailSender, DisabledEmailSender>();
        return services;
    }

    public static AppEmailProviderDiagnosticsDto GetDiagnostics(
        IConfiguration configuration,
        bool emailFeaturesEnabled,
        bool isProduction)
    {
        var mode = ReadConfiguredEmailMode(configuration, isProduction);
        var smtp = ReadSmtpOptions(configuration);
        var problems = new List<string>();
        if (isProduction && emailFeaturesEnabled && !mode.Equals("Smtp", StringComparison.OrdinalIgnoreCase))
        {
            problems.Add("Production email-dependent flows require AppForge:Email:Mode=Smtp.");
        }
        if (mode.Equals("Smtp", StringComparison.OrdinalIgnoreCase))
        {
            AddSmtpValidationProblems(smtp, problems);
        }
        else if (!mode.Equals("LogOnly", StringComparison.OrdinalIgnoreCase) && !mode.Equals("Disabled", StringComparison.OrdinalIgnoreCase))
        {
            problems.Add("AppForge:Email:Mode must be Smtp, LogOnly or Disabled.");
        }

        return new AppEmailProviderDiagnosticsDto
        {
            Mode = mode,
            IsProduction = isProduction,
            EmailFeaturesEnabled = emailFeaturesEnabled,
            SmtpConfigured = mode.Equals("Smtp", StringComparison.OrdinalIgnoreCase) && problems.Count == 0,
            HostConfigured = !string.IsNullOrWhiteSpace(smtp.Host),
            Port = smtp.Port,
            FromConfigured = !string.IsNullOrWhiteSpace(smtp.From),
            UserNameConfigured = !string.IsNullOrWhiteSpace(smtp.UserName),
            PasswordConfigured = !string.IsNullOrWhiteSpace(smtp.Password),
            EnableSsl = smtp.EnableSsl,
            Problems = problems.ToArray(),
        };
    }

    public static SmtpEmailOptions ReadSmtpOptions(IConfiguration configuration)
    {
        var options = new SmtpEmailOptions();
        configuration.GetSection("AppForge:Email:Smtp").Bind(options);
        return options;
    }

    private static string ReadConfiguredEmailMode(IConfiguration configuration, bool isProduction)
    {
        return configuration["AppForge:Email:Mode"] ?? (isProduction ? "Disabled" : "LogOnly");
    }

    private static void AddSmtpValidationProblems(SmtpEmailOptions options, List<string> problems)
    {
        if (string.IsNullOrWhiteSpace(options.Host))
        {
            problems.Add("SMTP email mode requires AppForge:Email:Smtp:Host.");
        }
        if (options.Port <= 0 || options.Port > 65535)
        {
            problems.Add("SMTP email mode requires AppForge:Email:Smtp:Port between 1 and 65535.");
        }
        if (string.IsNullOrWhiteSpace(options.From))
        {
            problems.Add("SMTP email mode requires AppForge:Email:Smtp:From.");
        }
        if (string.IsNullOrWhiteSpace(options.UserName) != string.IsNullOrWhiteSpace(options.Password))
        {
            problems.Add("SMTP email mode requires AppForge:Email:Smtp:UserName and Password to be configured together.");
        }
    }
}
