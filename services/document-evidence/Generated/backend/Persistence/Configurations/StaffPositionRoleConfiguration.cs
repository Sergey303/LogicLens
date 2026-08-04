using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class StaffPositionRoleConfiguration : IEntityTypeConfiguration<StaffPositionRole>
{
    public void Configure(EntityTypeBuilder<StaffPositionRole> builder)
    {
        builder.ToTable("StaffPositionRoles");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.StaffPositionId).IsRequired();
        builder.Property(x => x.RoleId).IsRequired();
        builder.HasOne(x => x.StaffPosition)
            .WithMany(x => x.StaffPositionRoles)
            .HasForeignKey(x => x.StaffPositionId)
            .IsRequired();
        builder.HasOne(x => x.Role)
            .WithMany(x => x.StaffPositionRoles)
            .HasForeignKey(x => x.RoleId)
            .IsRequired();
        builder.HasIndex(x => new { x.StaffPositionId, x.RoleId })
            .HasDatabaseName("IX_StaffPositionRoles_StaffPositionId_RoleId")
            .IsUnique();
        builder.HasIndex(x => x.RoleId)
            .HasDatabaseName("IX_StaffPositionRoles_RoleId");
    }
}
