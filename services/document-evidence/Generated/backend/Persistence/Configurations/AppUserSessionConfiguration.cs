#nullable enable

using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class AppUserSessionConfiguration : IEntityTypeConfiguration<AppUserSession>
{
    public void Configure(EntityTypeBuilder<AppUserSession> builder)
    {
        builder.ToTable("AppUserSessions");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.AppUserId).IsRequired();
        builder.Property(x => x.AccessTokenHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.RefreshTokenHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.AccessTokenExpiresAtUtc).IsRequired();
        builder.Property(x => x.RefreshTokenExpiresAtUtc).IsRequired();
        builder.Property(x => x.RevokedAtUtc);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.AccessTokenHash).IsUnique();
        builder.HasIndex(x => x.RefreshTokenHash).IsUnique();
        builder.HasIndex(x => x.AppUserId);
    }
}

public sealed class AuthLoginAttemptConfiguration : IEntityTypeConfiguration<AuthLoginAttempt>
{
    public void Configure(EntityTypeBuilder<AuthLoginAttempt> builder)
    {
        builder.ToTable("AuthLoginAttempts");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.LoginHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.IpHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.Succeeded).IsRequired();
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.LoginHash);
        builder.HasIndex(x => x.IpHash);
        builder.HasIndex(x => x.CreatedAtUtc);
    }
}

public sealed class PasswordResetTokenConfiguration : IEntityTypeConfiguration<PasswordResetToken>
{
    public void Configure(EntityTypeBuilder<PasswordResetToken> builder)
    {
        builder.ToTable("PasswordResetTokens");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.AppUserId).IsRequired();
        builder.Property(x => x.TokenHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.ExpiresAtUtc).IsRequired();
        builder.Property(x => x.UsedAtUtc);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.TokenHash).IsUnique();
        builder.HasIndex(x => x.AppUserId);
    }
}

public sealed class AccountRecoveryAttemptConfiguration : IEntityTypeConfiguration<AccountRecoveryAttempt>
{
    public void Configure(EntityTypeBuilder<AccountRecoveryAttempt> builder)
    {
        builder.ToTable("AccountRecoveryAttempts");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.EmailHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.IpHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.EmailHash);
        builder.HasIndex(x => x.IpHash);
        builder.HasIndex(x => x.CreatedAtUtc);
    }
}

public sealed class UserInvitationConfiguration : IEntityTypeConfiguration<UserInvitation>
{
    public void Configure(EntityTypeBuilder<UserInvitation> builder)
    {
        builder.ToTable("UserInvitations");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Email).IsRequired().HasMaxLength(320);
        builder.Property(x => x.TokenHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.RoleCodes).IsRequired().HasMaxLength(1000);
        builder.Property(x => x.ExpiresAtUtc).IsRequired();
        builder.Property(x => x.AcceptedAtUtc);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.TokenHash).IsUnique();
        builder.HasIndex(x => x.Email);
    }
}

public sealed class EmailConfirmationTokenConfiguration : IEntityTypeConfiguration<EmailConfirmationToken>
{
    public void Configure(EntityTypeBuilder<EmailConfirmationToken> builder)
    {
        builder.ToTable("EmailConfirmationTokens");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.AppUserId).IsRequired();
        builder.Property(x => x.TokenHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.ExpiresAtUtc).IsRequired();
        builder.Property(x => x.UsedAtUtc);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.TokenHash).IsUnique();
        builder.HasIndex(x => x.AppUserId);
    }
}

public sealed class IdentityAuditLogConfiguration : IEntityTypeConfiguration<IdentityAuditLog>
{
    public void Configure(EntityTypeBuilder<IdentityAuditLog> builder)
    {
        builder.ToTable("IdentityAuditLogs");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.Property(x => x.Action).IsRequired().HasMaxLength(120);
        builder.Property(x => x.ActorUserId);
        builder.Property(x => x.ActorEmail).IsRequired().HasMaxLength(320);
        builder.Property(x => x.TargetUserId);
        builder.Property(x => x.TargetEmail).IsRequired().HasMaxLength(320);
        builder.Property(x => x.Details).IsRequired().HasMaxLength(1000);
        builder.HasIndex(x => x.CreatedAtUtc);
        builder.HasIndex(x => x.Action);
        builder.HasIndex(x => x.ActorUserId);
        builder.HasIndex(x => x.TargetUserId);
    }
}
