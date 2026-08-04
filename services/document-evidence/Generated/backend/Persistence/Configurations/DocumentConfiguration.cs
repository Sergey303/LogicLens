using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class DocumentConfiguration : IEntityTypeConfiguration<Document>
{
    public void Configure(EntityTypeBuilder<Document> builder)
    {
        builder.ToTable("Documents");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.WorkspaceId).IsRequired();
        builder.Property(x => x.DisplayName).IsRequired();
        builder.Property(x => x.DisplayName).HasMaxLength(260);
        builder.Property(x => x.MediaType).IsRequired();
        builder.Property(x => x.MediaType).HasMaxLength(120);
        builder.Property(x => x.SourceKind).IsRequired();
        builder.Property(x => x.SourceKind).HasMaxLength(40);
        builder.Property(x => x.State).IsRequired();
        builder.Property(x => x.State).HasMaxLength(40);
        builder.Property(x => x.CurrentRevisionNumber).IsRequired();
        builder.Property(x => x.IsRevoked).IsRequired();
        builder.Property(x => x.CreationTime).IsRequired();
        builder.Property(x => x.IsDeleted).IsRequired().HasDefaultValue(false);
        builder.HasQueryFilter(x => !x.IsDeleted);
        builder.HasIndex(x => x.IsDeleted)
            .HasDatabaseName("IX_Documents_IsDeleted");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.CreatorPositionId);
        builder.HasIndex(x => x.CreatorPositionId)
            .HasDatabaseName("IX_Documents_CreatorPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.LastModifierPositionId);
        builder.HasIndex(x => x.LastModifierPositionId)
            .HasDatabaseName("IX_Documents_LastModifierPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.DeleterPositionId);
        builder.HasIndex(x => x.DeleterPositionId)
            .HasDatabaseName("IX_Documents_DeleterPositionId");
        builder.Property(x => x.DisplayNameSearch).IsRequired();
        builder.Property(x => x.DisplayNameSearch).HasMaxLength(260);
        builder.Property(x => x.MediaTypeSearch).IsRequired();
        builder.Property(x => x.MediaTypeSearch).HasMaxLength(120);
        builder.Property(x => x.SourceKindSearch).IsRequired();
        builder.Property(x => x.SourceKindSearch).HasMaxLength(40);
        builder.Property(x => x.StateSearch).IsRequired();
        builder.Property(x => x.StateSearch).HasMaxLength(40);
        builder.HasIndex(x => new { x.WorkspaceId, x.DisplayName })
            .HasDatabaseName("IX_Documents_WorkspaceId_DisplayName");
        builder.HasIndex(x => new { x.WorkspaceId, x.State })
            .HasDatabaseName("IX_Documents_WorkspaceId_State");
        builder.HasIndex(x => x.DisplayNameSearch)
            .HasDatabaseName("IX_Documents_DisplayNameSearch");
        builder.HasIndex(x => x.MediaTypeSearch)
            .HasDatabaseName("IX_Documents_MediaTypeSearch");
        builder.HasIndex(x => x.SourceKindSearch)
            .HasDatabaseName("IX_Documents_SourceKindSearch");
        builder.HasIndex(x => x.StateSearch)
            .HasDatabaseName("IX_Documents_StateSearch");
    }
}
