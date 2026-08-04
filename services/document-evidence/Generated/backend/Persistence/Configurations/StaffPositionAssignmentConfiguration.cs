using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class StaffPositionAssignmentConfiguration : IEntityTypeConfiguration<StaffPositionAssignment>
{
    public void Configure(EntityTypeBuilder<StaffPositionAssignment> builder)
    {
        builder.ToTable("StaffPositionAssignments");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.StaffPositionId).IsRequired();
        builder.Property(x => x.UserId).IsRequired();
        builder.Property(x => x.AssignmentKind).IsRequired();
        builder.Property(x => x.AssignmentKind).HasMaxLength(32);
        builder.Property(x => x.StartsAt).IsRequired();
        builder.Property(x => x.StartsAtUtc).IsRequired();
        builder.Property(x => x.IsActive).IsRequired();
        builder.Property(x => x.Reason).HasMaxLength(500);
        builder.HasOne(x => x.StaffPosition)
            .WithMany(x => x.StaffPositionAssignments)
            .HasForeignKey(x => x.StaffPositionId)
            .IsRequired();
        builder.HasIndex(x => x.StaffPositionId)
            .HasDatabaseName("IX_StaffPositionAssignments_StaffPositionId");
        builder.HasIndex(x => x.UserId)
            .HasDatabaseName("IX_StaffPositionAssignments_UserId");
        builder.HasIndex(x => x.IsActive)
            .HasDatabaseName("IX_StaffPositionAssignments_IsActive");
        builder.HasIndex(x => new { x.UserId, x.StaffPositionId, x.IsActive })
            .HasDatabaseName("IX_StaffPositionAssignments_UserId_StaffPositionId_IsActive");
    }
}
