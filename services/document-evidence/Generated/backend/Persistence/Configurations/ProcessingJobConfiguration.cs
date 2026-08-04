using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class ProcessingJobConfiguration : IEntityTypeConfiguration<ProcessingJob>
{
    public void Configure(EntityTypeBuilder<ProcessingJob> builder)
    {
        builder.ToTable("ProcessingJobs");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.DocumentRevisionId).IsRequired();
        builder.Property(x => x.Kind).IsRequired();
        builder.Property(x => x.Kind).HasMaxLength(80);
        builder.Property(x => x.State).IsRequired();
        builder.Property(x => x.State).HasMaxLength(40);
        builder.Property(x => x.Attempt).IsRequired();
        builder.Property(x => x.IdempotencyKey).IsRequired();
        builder.Property(x => x.IdempotencyKey).HasMaxLength(160);
        builder.Property(x => x.LastErrorCode).HasMaxLength(120);
        builder.Property(x => x.CreationTime).IsRequired();
        builder.Property(x => x.IsDeleted).IsRequired().HasDefaultValue(false);
        builder.HasQueryFilter(x => !x.IsDeleted);
        builder.HasIndex(x => x.IsDeleted)
            .HasDatabaseName("IX_ProcessingJobs_IsDeleted");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.CreatorPositionId);
        builder.HasIndex(x => x.CreatorPositionId)
            .HasDatabaseName("IX_ProcessingJobs_CreatorPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.LastModifierPositionId);
        builder.HasIndex(x => x.LastModifierPositionId)
            .HasDatabaseName("IX_ProcessingJobs_LastModifierPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.DeleterPositionId);
        builder.HasIndex(x => x.DeleterPositionId)
            .HasDatabaseName("IX_ProcessingJobs_DeleterPositionId");
        builder.Property(x => x.KindSearch).IsRequired();
        builder.Property(x => x.KindSearch).HasMaxLength(80);
        builder.Property(x => x.StateSearch).IsRequired();
        builder.Property(x => x.StateSearch).HasMaxLength(40);
        builder.Property(x => x.IdempotencyKeySearch).IsRequired();
        builder.Property(x => x.IdempotencyKeySearch).HasMaxLength(160);
        builder.Property(x => x.LastErrorCodeSearch).IsRequired();
        builder.Property(x => x.LastErrorCodeSearch).HasMaxLength(120);
        builder.HasOne(x => x.DocumentRevision)
            .WithMany(x => x.ProcessingJobs)
            .HasForeignKey(x => x.DocumentRevisionId)
            .IsRequired();
        builder.HasIndex(x => x.IdempotencyKey)
            .HasDatabaseName("UX_ProcessingJobs_IdempotencyKey")
            .IsUnique();
        builder.HasIndex(x => new { x.State, x.LeaseUntil })
            .HasDatabaseName("IX_ProcessingJobs_State_LeaseUntil");
        builder.HasIndex(x => x.KindSearch)
            .HasDatabaseName("IX_ProcessingJobs_KindSearch");
        builder.HasIndex(x => x.StateSearch)
            .HasDatabaseName("IX_ProcessingJobs_StateSearch");
        builder.HasIndex(x => x.IdempotencyKeySearch)
            .HasDatabaseName("IX_ProcessingJobs_IdempotencyKeySearch");
        builder.HasIndex(x => x.LastErrorCodeSearch)
            .HasDatabaseName("IX_ProcessingJobs_LastErrorCodeSearch");
    }
}
