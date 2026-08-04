using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class StoredObjectConfiguration : IEntityTypeConfiguration<StoredObject>
{
    public void Configure(EntityTypeBuilder<StoredObject> builder)
    {
        builder.ToTable("StoredObjects");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.Id).IsRequired();
        builder.Property(x => x.Sha256).IsRequired();
        builder.Property(x => x.Sha256).HasMaxLength(64);
        builder.Property(x => x.StorageKey).IsRequired();
        builder.Property(x => x.StorageKey).HasMaxLength(512);
        builder.Property(x => x.SizeBytes).IsRequired();
        builder.Property(x => x.MediaType).IsRequired();
        builder.Property(x => x.MediaType).HasMaxLength(120);
        builder.Property(x => x.CreationTime).IsRequired();
        builder.Property(x => x.IsDeleted).IsRequired().HasDefaultValue(false);
        builder.HasQueryFilter(x => !x.IsDeleted);
        builder.HasIndex(x => x.IsDeleted)
            .HasDatabaseName("IX_StoredObjects_IsDeleted");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.CreatorPositionId);
        builder.HasIndex(x => x.CreatorPositionId)
            .HasDatabaseName("IX_StoredObjects_CreatorPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.LastModifierPositionId);
        builder.HasIndex(x => x.LastModifierPositionId)
            .HasDatabaseName("IX_StoredObjects_LastModifierPositionId");
        builder.HasOne<StaffPosition>()
            .WithMany()
            .HasForeignKey(x => x.DeleterPositionId);
        builder.HasIndex(x => x.DeleterPositionId)
            .HasDatabaseName("IX_StoredObjects_DeleterPositionId");
        builder.Property(x => x.Sha256Search).IsRequired();
        builder.Property(x => x.Sha256Search).HasMaxLength(64);
        builder.Property(x => x.StorageKeySearch).IsRequired();
        builder.Property(x => x.StorageKeySearch).HasMaxLength(512);
        builder.Property(x => x.MediaTypeSearch).IsRequired();
        builder.Property(x => x.MediaTypeSearch).HasMaxLength(120);
        builder.HasIndex(x => x.Sha256)
            .HasDatabaseName("UX_StoredObjects_Sha256")
            .IsUnique();
        builder.HasIndex(x => x.Sha256Search)
            .HasDatabaseName("IX_StoredObjects_Sha256Search");
        builder.HasIndex(x => x.StorageKeySearch)
            .HasDatabaseName("IX_StoredObjects_StorageKeySearch");
        builder.HasIndex(x => x.MediaTypeSearch)
            .HasDatabaseName("IX_StoredObjects_MediaTypeSearch");
    }
}
