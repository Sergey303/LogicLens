using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace LogicLens.DocumentEvidence.Generated.Persistence;

public sealed class DocumentEvidenceOperationalModelDbContextFactory : IDesignTimeDbContextFactory<DocumentEvidenceOperationalModelDbContext>
{
    public DocumentEvidenceOperationalModelDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable("APPFORGE_EF_CONNECTION_STRING")
            ?? "Host=localhost;Port=5432;Database=document_evidence_operational_model;Username=appforge;Password=appforge";
        var options = new DbContextOptionsBuilder<DocumentEvidenceOperationalModelDbContext>();
        options.UseNpgsql(connectionString);

        return new DocumentEvidenceOperationalModelDbContext(options.Options);
    }
}
