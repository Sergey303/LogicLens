using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;

namespace LogicLens.DocumentEvidence.Generated.Persistence;

public sealed class DocumentEvidenceOperationalModelDbContext : DbContext
{
    public DocumentEvidenceOperationalModelDbContext(DbContextOptions<DocumentEvidenceOperationalModelDbContext> options)
        : base(options)
    {
    }

    public DbSet<Document> Documents => Set<Document>();
    public DbSet<StoredObject> StoredObjects => Set<StoredObject>();
    public DbSet<DocumentRevision> DocumentRevisions => Set<DocumentRevision>();
    public DbSet<ProcessingJob> ProcessingJobs => Set<ProcessingJob>();
    public DbSet<DocumentFragment> DocumentFragments => Set<DocumentFragment>();
    public DbSet<Role> Roles => Set<Role>();
    public DbSet<Permission> Permissions => Set<Permission>();
    public DbSet<RolePermission> RolePermissions => Set<RolePermission>();
    public DbSet<StaffPosition> StaffPositions => Set<StaffPosition>();
    public DbSet<StaffPositionRole> StaffPositionRoles => Set<StaffPositionRole>();
    public DbSet<StaffPositionAssignment> StaffPositionAssignments => Set<StaffPositionAssignment>();
    public DbSet<AppUser> AppUsers => Set<AppUser>();
    public DbSet<AppUserRole> AppUserRoles => Set<AppUserRole>();
    public DbSet<AppUserSession> AppUserSessions => Set<AppUserSession>();
    public DbSet<AuthLoginAttempt> AuthLoginAttempts => Set<AuthLoginAttempt>();
    public DbSet<PasswordResetToken> PasswordResetTokens => Set<PasswordResetToken>();
    public DbSet<AccountRecoveryAttempt> AccountRecoveryAttempts => Set<AccountRecoveryAttempt>();
    public DbSet<PublicRegistrationAttempt> PublicRegistrationAttempts => Set<PublicRegistrationAttempt>();
    public DbSet<UserInvitation> UserInvitations => Set<UserInvitation>();
    public DbSet<EmailConfirmationToken> EmailConfirmationTokens => Set<EmailConfirmationToken>();
    public DbSet<IdentityAuditLog> IdentityAuditLogs => Set<IdentityAuditLog>();
    public DbSet<AppForgeSeedHistory> AppForgeSeedHistory => Set<AppForgeSeedHistory>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        modelBuilder.ApplyConfiguration(new Configurations.DocumentConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.StoredObjectConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.DocumentRevisionConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.ProcessingJobConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.DocumentFragmentConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.RoleConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.PermissionConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.RolePermissionConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.StaffPositionConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.StaffPositionRoleConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.StaffPositionAssignmentConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AppUserConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AppUserRoleConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AppUserSessionConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AuthLoginAttemptConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.PasswordResetTokenConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AccountRecoveryAttemptConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.PublicRegistrationAttemptConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.UserInvitationConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.EmailConfirmationTokenConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.IdentityAuditLogConfiguration());
        modelBuilder.ApplyConfiguration(new Configurations.AppForgeSeedHistoryConfiguration());
    }
}
