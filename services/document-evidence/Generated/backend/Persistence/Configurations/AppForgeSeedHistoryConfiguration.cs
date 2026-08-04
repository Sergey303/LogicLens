using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class AppForgeSeedHistoryConfiguration : IEntityTypeConfiguration<AppForgeSeedHistory>
{
    public void Configure(EntityTypeBuilder<AppForgeSeedHistory> builder)
    {
        builder.ToTable("__AppForgeSeedHistory");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.ModelId).IsRequired().HasMaxLength(200);
        builder.Property(x => x.ModelVersion).IsRequired().HasMaxLength(100);
        builder.Property(x => x.SeedSetName).IsRequired().HasMaxLength(200);
        builder.Property(x => x.TableName).IsRequired().HasMaxLength(200);
        builder.Property(x => x.SourceMdHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.SeedHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.AppliedAt).IsRequired();
        builder.HasIndex(x => new { x.ModelId, x.ModelVersion, x.SeedSetName, x.TableName })
            .HasDatabaseName("IX___AppForgeSeedHistory_Model_SeedSet_Table")
            .IsUnique();
    }
}
