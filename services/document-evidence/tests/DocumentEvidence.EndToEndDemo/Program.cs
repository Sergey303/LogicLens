using System.Text.Json;
using KnowledgePilot.LogicLens.DocumentEvidence.Client;

namespace KnowledgePilot.LogicLens.DocumentEvidence.EndToEndDemo;

internal static class Program
{
    private static readonly Guid ActorId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid WorkspaceId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static readonly Guid DocumentId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");
    private static readonly JsonSerializerOptions Json = new() { WriteIndented = true };

    public static async Task<int> Main(string[] args)
    {
        var outputRoot = Path.GetFullPath(
            args.Length == 1
                ? args[0]
                : Path.Combine(".artifacts", "document-evidence", "eng-148-service")
        );
        Directory.CreateDirectory(outputRoot);
        var pdfBytes = DemoPdfFixture.Create();
        await File.WriteAllBytesAsync(Path.Combine(outputRoot, "demo.pdf"), pdfBytes);

        await using var host = await DemoServiceHost.StartAsync(
            Path.Combine(outputRoot, "objects")
        );
        var client = new DocumentEvidenceClient(host.Client, ActorId);
        using var content = new MemoryStream(pdfBytes, writable: false);
        var upload = await client.UploadRevisionAsync(
            WorkspaceId,
            DocumentId,
            "demo.pdf",
            "eng-148-demo-v1",
            "application/pdf",
            content,
            pdfBytes.LongLength
        );
        var metadata = await client.GetDocumentAsync(WorkspaceId, DocumentId)
            ?? throw new InvalidDataException("Uploaded demo document was not found through the client.");
        var fragments = await client.ListFragmentsAsync(WorkspaceId, upload.RevisionId);
        var selected = fragments.Single(fragment =>
            fragment.Text.Contains(DemoPdfFixture.Quote, StringComparison.Ordinal)
        );
        var fragmentBytes = DemoSourceFragment.Export(upload, selected);
        var fragmentPath = Path.Combine(outputRoot, "selected-fragment.jsonl");
        await File.WriteAllBytesAsync(fragmentPath, fragmentBytes);

        var openApiBytes = await File.ReadAllBytesAsync(
            Path.Combine("services", "document-evidence", "openapi", "document-evidence-v1.json")
        );
        var receipt = new
        {
            schemaVersion = "0.1",
            scenario = "eng-148-pdf-client-fragment",
            openApiSha256 = $"sha256:{DemoIdentity.Sha256(openApiBytes)}",
            pdfSha256 = $"sha256:{DemoIdentity.Sha256(pdfBytes)}",
            upload.WorkspaceId,
            upload.DocumentId,
            upload.RevisionId,
            upload.RevisionNumber,
            upload.ManifestSha256,
            upload.ProcessingState,
            metadata.State,
            fragmentCount = fragments.Count,
            selectedFragmentId = selected.FragmentId,
            selected.ContentSha256,
            selectedFragmentSha256 = $"sha256:{DemoIdentity.Sha256(fragmentBytes)}",
            parserVersion = selected.Anchor.Value.GetProperty("parserVersion").GetString(),
            consumerReadsDatabase = false,
            consumerReadsBlobPath = false,
        };
        var receiptBytes = JsonSerializer.SerializeToUtf8Bytes(receipt, Json);
        var receiptPath = Path.Combine(outputRoot, "service-receipt.json");
        await File.WriteAllBytesAsync(receiptPath, receiptBytes);
        Console.WriteLine(JsonSerializer.Serialize(receipt, Json));
        return 0;
    }
}
