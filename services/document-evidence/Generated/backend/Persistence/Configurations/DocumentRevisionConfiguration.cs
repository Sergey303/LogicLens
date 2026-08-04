using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class DocumentRevisionConfiguration : IEntityTypeConfiguration<DocumentRevision>
{
    public void Configure(EntityTypeBuilder<DocumentRevision> builder)
    {
        builder.ToTable("DocumentRevisions");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.DocumentId).IsRequired();
        builder.Property(x => x.StoredObjectId).IsRequired();
        builder.Property(x => x.RevisionNumber).IsRequired();
        builder.Property(x => x.State).IsRequired();
        builder.Property(x => x.State).HasMaxLength(40);
        builder.Property(x => x.Adapter).HasMaxLength(120);
        builder.Property(x => x.AdapterVersion).HasMaxLength(80);
        builder.Property(x => x.ManifestHash).HasMaxLength(64);
        builder.Property(x => x.CreationTime).IsRequired();
        builder.Property(x => x.IsDeleted).IsRequired().HasDefaultValue(false);
        builder.HasQueryFilter(x => !x.IsDeleted);
        builder.HasIndex(x => x.IsDeleted)
            .HasDatabaseName("IX_DocumentRevisions_IsDeleted");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.CreatorPositionId);
        builder.HasIndex(x => x.CreatorPositionId)
            .HasDatabaseName("IX_DocumentRevisions_CreatorPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.LastModifierPositionId);
        builder.HasIndex(x => x.LastModifierPositionId)
            .HasDatabaseName("IX_DocumentRevisions_LastModifierPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.DeleterPositionId);
        builder.HasIndex(x => x.DeleterPositionId)
            .HasDatabaseName("IX_DocumentRevisions_DeleterPositionId");
        builder.Property(x => x.StateSearch).IsRequired();
        builder.Property(x => x.StateSearch).HasMaxLength(40);
        builder.Property(x => x.AdapterSearch).IsRequired();
        builder.Property(x => x.AdapterSearch).HasMaxLength(120);
        builder.Property(x => x.AdapterVersionSearch).IsRequired();
        builder.Property(x => x.AdapterVersionSearch).HasMaxLength(80);
        builder.Property(x => x.ManifestHashSearch).IsRequired();
        builder.Property(x => x.ManifestHashSearch).HasMaxLength(64);
        builder.HasOne(x => x.Document)
            .WithMany(x => x.Revisions)
            .HasForeignKey(x => x.DocumentId)
            .IsRequired();
        builder.HasOne(x => x.StoredObject)
            .WithMany(x => x.Revisions)
            .HasForeignKey(x => x.StoredObjectId)
            .IsRequired();
        builder.HasIndex(x => new { x.DocumentId, x.RevisionNumber })
            .HasDatabaseName("UX_DocumentRevisions_DocumentId_RevisionNumber")
            .IsUnique();
        builder.HasIndex(x => x.StateSearch)
            .HasDatabaseName("IX_DocumentRevisions_StateSearch");
        builder.HasIndex(x => x.AdapterSearch)
            .HasDatabaseName("IX_DocumentRevisions_AdapterSearch");
        builder.HasIndex(x => x.AdapterVersionSearch)
            .HasDatabaseName("IX_DocumentRevisions_AdapterVersionSearch");
        builder.HasIndex(x => x.ManifestHashSearch)
            .HasDatabaseName("IX_DocumentRevisions_ManifestHashSearch");
    }
}
