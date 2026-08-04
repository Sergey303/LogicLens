#nullable enable

using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class AppUserRoleConfiguration : IEntityTypeConfiguration<AppUserRole>
{
    public void Configure(EntityTypeBuilder<AppUserRole> builder)
    {
        builder.ToTable("AppUserRoles");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.AppUserId).IsRequired();
        builder.Property(x => x.RoleId).IsRequired();
        builder.HasIndex(x => new { x.AppUserId, x.RoleId }).IsUnique();
    }
}
