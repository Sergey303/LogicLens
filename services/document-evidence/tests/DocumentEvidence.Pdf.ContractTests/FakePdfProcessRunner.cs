using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal sealed class FakePdfProcessRunner : IPdfProcessRunner
{
    public List<(string Executable, IReadOnlyList<string> Arguments)> Calls { get; } = [];

    public Task<PdfProcessResult> RunAsync(
        string executable,
        IReadOnlyList<string> arguments,
        string workingDirectory,
        CancellationToken cancellationToken
    )
    {
        Calls.Add((executable, arguments.ToArray()));
        if (!Directory.Exists(workingDirectory))
        {
            throw new InvalidOperationException("Adapter did not create an isolated workspace.");
        }
        if (arguments.SequenceEqual(["-v"]))
        {
            return Task.FromResult(new PdfProcessResult(0, "", "pdftotext version 25.03.0"));
        }
        if (executable.Contains("pdfinfo", StringComparison.OrdinalIgnoreCase))
        {
            DemandSource(arguments.Single());
            return Task.FromResult(new PdfProcessResult(0, PdfTestFixture.PdfInfo, ""));
        }
        if (arguments.Contains("-bbox-layout", StringComparer.Ordinal))
        {
            DemandSource(arguments[^2]);
            return Task.FromResult(new PdfProcessResult(0, PdfTestFixture.BboxXhtml, ""));
        }
        throw new InvalidOperationException("Unexpected PDF process invocation.");
    }

    private static void DemandSource(string path)
    {
        var bytes = File.ReadAllBytes(path);
        if (!bytes.AsSpan().StartsWith("%PDF-"u8))
        {
            throw new InvalidOperationException("Poppler received unvalidated source bytes.");
        }
    }
}
