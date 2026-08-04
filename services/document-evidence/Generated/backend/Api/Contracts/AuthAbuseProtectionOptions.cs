#nullable enable

using System.Security.Cryptography;
using System.Text;

namespace LogicLens.DocumentEvidence.Generated.Api.Contracts;

public sealed class AppAuthAbuseProtectionOptions
{
    public bool RegistrationAbuseProtectionEnabled { get; set; } = true;
    public int RegistrationEmailLimitPerHour { get; set; } = 3;
    public int RegistrationIpLimitPerHour { get; set; } = 10;
}

public static class AuthAbuseProtectionOptionsExtensions
{
    public static AppAuthAbuseProtectionOptions ReadOptions(IConfiguration configuration)
    {
        var options = new AppAuthAbuseProtectionOptions();
        configuration.GetSection("AppForge:Auth:AbuseProtection").Bind(options);
        if (options.RegistrationEmailLimitPerHour <= 0)
        {
            options.RegistrationEmailLimitPerHour = 3;
        }
        if (options.RegistrationIpLimitPerHour <= 0)
        {
            options.RegistrationIpLimitPerHour = 10;
        }
        return options;
    }
}

public static class AuthCodeDigest
{
    public const string AccessPurpose = "access";
    public const string RefreshPurpose = "refresh";
    public const string RecoveryPurpose = "recovery";
    public const string ConfirmationPurpose = "confirmation";
    public const string InvitationPurpose = "invitation";

    public static string NewCode(int byteCount = 64)
    {
        return Convert.ToHexString(RandomNumberGenerator.GetBytes(byteCount));
    }

    public static string Create(IConfiguration configuration, string purpose, string value)
    {
        var material = Encoding.UTF8.GetBytes(purpose + "\n" + value);
        var key = configuration["AppForge:Auth:CodeDigestKey"];
        if (string.IsNullOrWhiteSpace(key))
        {
            return Convert.ToHexString(SHA256.HashData(material));
        }

        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(key));
        return Convert.ToHexString(hmac.ComputeHash(material));
    }

    public static bool HasKey(IConfiguration configuration)
    {
        return !string.IsNullOrWhiteSpace(configuration["AppForge:Auth:CodeDigestKey"]);
    }
}
