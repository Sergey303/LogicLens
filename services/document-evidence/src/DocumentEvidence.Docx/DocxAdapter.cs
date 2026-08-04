using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Docx;

public sealed class DocxAdapter
{
    private const string AdapterName = "docx-ooxml";
    private const string AdapterVersion = "1.0.0";
    private const string OfficeDocumentRelationship =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument";
    private const string MainDocumentContentType =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml";

    public async Task<DocxDocument> ExtractAsync(
        Stream source,
        OoxmlPackageLimits? limits = null,
        CancellationToken cancellationToken = default
    )
    {
        var package = await OoxmlPackageReader.ReadAsync(source, limits, cancellationToken);
        var relationships = OoxmlRelationships.Read(package, "_rels/.rels", "");
        var documentPartName = OoxmlRelationships.DemandSingleTargetByType(
            relationships,
            OfficeDocumentRelationship
        );
        OoxmlContentTypes.DemandOverride(
            package,
            documentPartName,
            MainDocumentContentType
        );
        var blocks = DocxBodyParser.Parse(package.RequirePart(documentPartName));
        var irHash = OoxmlHashing.Sha256(JsonSerializer.SerializeToUtf8Bytes(new
        {
            adapter = AdapterName,
            version = AdapterVersion,
            package = package.Identity.EntriesSha256,
            metadata = package.Identity.CoreProperties,
            blocks,
        }));
        return new DocxDocument(
            AdapterName,
            AdapterVersion,
            package.Identity.ArtifactSha256,
            package.Identity.EntriesSha256,
            irHash,
            package.Identity.CoreProperties,
            blocks
        );
    }
}
