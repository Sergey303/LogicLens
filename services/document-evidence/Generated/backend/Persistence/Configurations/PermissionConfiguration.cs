using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class PermissionConfiguration : IEntityTypeConfiguration<Permission>
{
    public void Configure(EntityTypeBuilder<Permission> builder)
    {
        builder.ToTable("Permissions");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.Code).IsRequired();
        builder.Property(x => x.Code).HasMaxLength(200);
        builder.Property(x => x.Name).IsRequired();
        builder.Property(x => x.Name).HasMaxLength(200);
        builder.HasIndex(x => x.Code)
            .HasDatabaseName("IX_Permissions_Code")
            .IsUnique();
    }
}
