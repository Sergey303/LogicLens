using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class DocumentFragmentConfiguration : IEntityTypeConfiguration<DocumentFragment>
{
    public void Configure(EntityTypeBuilder<DocumentFragment> builder)
    {
        builder.ToTable("DocumentFragments");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.DocumentRevisionId).IsRequired();
        builder.Property(x => x.Sequence).IsRequired();
        builder.Property(x => x.Kind).IsRequired();
        builder.Property(x => x.Kind).HasMaxLength(40);
        builder.Property(x => x.AnchorJson).IsRequired();
        builder.Property(x => x.AnchorJson).HasMaxLength(2000);
        builder.Property(x => x.Text).IsRequired();
        builder.Property(x => x.Text).HasMaxLength(8000);
        builder.Property(x => x.ContentHash).IsRequired();
        builder.Property(x => x.ContentHash).HasMaxLength(64);
        builder.Property(x => x.CreationTime).IsRequired();
        builder.Property(x => x.IsDeleted).IsRequired().HasDefaultValue(false);
        builder.HasQueryFilter(x => !x.IsDeleted);
        builder.HasIndex(x => x.IsDeleted)
            .HasDatabaseName("IX_DocumentFragments_IsDeleted");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.CreatorPositionId);
        builder.HasIndex(x => x.CreatorPositionId)
            .HasDatabaseName("IX_DocumentFragments_CreatorPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.LastModifierPositionId);
        builder.HasIndex(x => x.LastModifierPositionId)
            .HasDatabaseName("IX_DocumentFragments_LastModifierPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.DeleterPositionId);
        builder.HasIndex(x => x.DeleterPositionId)
            .HasDatabaseName("IX_DocumentFragments_DeleterPositionId");
        builder.Property(x => x.KindSearch).IsRequired();
        builder.Property(x => x.KindSearch).HasMaxLength(40);
        builder.Property(x => x.AnchorJsonSearch).IsRequired();
        builder.Property(x => x.AnchorJsonSearch).HasMaxLength(2000);
        builder.Property(x => x.TextSearch).IsRequired();
        builder.Property(x => x.TextSearch).HasMaxLength(8000);
        builder.Property(x => x.ContentHashSearch).IsRequired();
        builder.Property(x => x.ContentHashSearch).HasMaxLength(64);
        builder.HasOne(x => x.DocumentRevision)
            .WithMany(x => x.Fragments)
            .HasForeignKey(x => x.DocumentRevisionId)
            .IsRequired();
        builder.HasIndex(x => new { x.DocumentRevisionId, x.Sequence })
            .HasDatabaseName("UX_DocumentFragments_Revision_Sequence")
            .IsUnique();
        builder.HasIndex(x => x.ContentHash)
            .HasDatabaseName("IX_DocumentFragments_ContentHash");
        builder.HasIndex(x => x.KindSearch)
            .HasDatabaseName("IX_DocumentFragments_KindSearch");
        builder.HasIndex(x => x.AnchorJsonSearch)
            .HasDatabaseName("IX_DocumentFragments_AnchorJsonSearch");
        builder.HasIndex(x => x.TextSearch)
            .HasDatabaseName("IX_DocumentFragments_TextSearch");
        builder.HasIndex(x => x.ContentHashSearch)
            .HasDatabaseName("IX_DocumentFragments_ContentHashSearch");
    }
}
