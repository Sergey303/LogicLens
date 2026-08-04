using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class StaffPositionConfiguration : IEntityTypeConfiguration<StaffPosition>
{
    public void Configure(EntityTypeBuilder<StaffPosition> builder)
    {
        builder.ToTable("StaffPositions");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.Code).IsRequired();
        builder.Property(x => x.Code).HasMaxLength(128);
        builder.Property(x => x.Name).IsRequired();
        builder.Property(x => x.Name).HasMaxLength(200);
        builder.Property(x => x.Description).HasMaxLength(1000);
        builder.Property(x => x.IsActive).IsRequired();
        builder.HasOne(x => x.ParentPosition)
            .WithMany(x => x.ChildPositions)
            .HasForeignKey(x => x.ParentPositionId);
        builder.HasIndex(x => x.Code)
            .HasDatabaseName("IX_StaffPositions_Code")
            .IsUnique();
        builder.HasIndex(x => x.ParentPositionId)
            .HasDatabaseName("IX_StaffPositions_ParentPositionId");
        builder.HasIndex(x => x.IsActive)
            .HasDatabaseName("IX_StaffPositions_IsActive");
    }
}
