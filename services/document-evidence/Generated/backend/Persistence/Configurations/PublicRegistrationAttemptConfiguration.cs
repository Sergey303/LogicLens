#nullable enable

using LogicLens.DocumentEvidence.Generated;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace LogicLens.DocumentEvidence.Generated.Persistence.Configurations;

public sealed class PublicRegistrationAttemptConfiguration : IEntityTypeConfiguration<PublicRegistrationAttempt>
{
    public void Configure(EntityTypeBuilder<PublicRegistrationAttempt> builder)
    {
        builder.ToTable("PublicRegistrationAttempts");
        builder.HasKey(x => x.Id);
        builder.Property(x => x.EmailHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.IpHash).IsRequired().HasMaxLength(128);
        builder.Property(x => x.Succeeded).IsRequired();
        builder.Property(x => x.CreatedAtUtc).IsRequired();
        builder.HasIndex(x => x.EmailHash);
        builder.HasIndex(x => x.IpHash);
        builder.HasIndex(x => x.CreatedAtUtc);
    }
}
