namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public sealed class PdfPopplerAdapter
{
    private static readonly string[] BboxArguments = ["-bbox-layout", "-enc", "UTF-8"];
    private readonly IPdfProcessRunner _runner;
    private readonly string _pdfInfoExecutable;
    private readonly string _pdfToTextExecutable;

    public PdfPopplerAdapter(
        IPdfProcessRunner runner,
        string pdfInfoExecutable = "pdfinfo",
        string pdfToTextExecutable = "pdftotext"
    )
    {
        _runner = runner ?? throw new ArgumentNullException(nameof(runner));
        ArgumentException.ThrowIfNullOrWhiteSpace(pdfInfoExecutable);
        ArgumentException.ThrowIfNullOrWhiteSpace(pdfToTextExecutable);
        _pdfInfoExecutable = pdfInfoExecutable;
        _pdfToTextExecutable = pdfToTextExecutable;
    }

    public async Task<PdfExtractionResult> ExtractAsync(
        Stream source,
        PdfExtractionRequest request,
        CancellationToken cancellationToken = default
    )
    {
        var input = await PdfInputValidator.ReadAsync(source, request, cancellationToken);
        var workspace = Path.Combine(Path.GetTempPath(), $"logiclens-pdf-{Guid.NewGuid():N}");
        Directory.CreateDirectory(workspace);
        try
        {
            var pdfPath = Path.Combine(workspace, "source.pdf");
            await WriteSourceAsync(pdfPath, input.Bytes, cancellationToken);
            var version = await ReadVersionAsync(workspace, cancellationToken);
            var info = await ReadInfoAsync(pdfPath, workspace, cancellationToken);
            var rawPages = await ReadBboxAsync(pdfPath, workspace, cancellationToken);
            var document = PdfDocumentFactory.Create(request, input, info, rawPages);
            var configurationSha256 = PdfHashing.CanonicalSha256(new
            {
                adapter = "poppler-bbox-layout",
                arguments = BboxArguments,
                blockSegmentation = "poppler-block-v1",
            });
            return new PdfExtractionResult(
                document,
                new PdfParserManifest(
                    "poppler-bbox-layout",
                    version,
                    configurationSha256,
                    input.Sha256,
                    document.IrSha256
                )
            );
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    private async Task<string> ReadVersionAsync(string workspace, CancellationToken cancellationToken)
    {
        var result = await _runner.RunAsync(
            _pdfToTextExecutable,
            ["-v"],
            workspace,
            cancellationToken
        );
        return PdfToolOutput.ParseVersion(result);
    }

    private async Task<PdfInfo> ReadInfoAsync(
        string pdfPath,
        string workspace,
        CancellationToken cancellationToken
    )
    {
        var result = await _runner.RunAsync(
            _pdfInfoExecutable,
            [pdfPath],
            workspace,
            cancellationToken
        );
        return PdfInfoParser.Parse(PdfToolOutput.DemandSuccess(result, "pdfinfo"));
    }

    private async Task<IReadOnlyList<PdfRawPage>> ReadBboxAsync(
        string pdfPath,
        string workspace,
        CancellationToken cancellationToken
    )
    {
        var arguments = BboxArguments.Concat([pdfPath, "-"]).ToList();
        var result = await _runner.RunAsync(
            _pdfToTextExecutable,
            arguments,
            workspace,
            cancellationToken
        );
        return PdfBboxParser.Parse(PdfToolOutput.DemandSuccess(result, "pdftotext"));
    }

    private static async Task WriteSourceAsync(
        string path,
        byte[] bytes,
        CancellationToken cancellationToken
    )
    {
        await using var stream = new FileStream(
            path,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            81920,
            FileOptions.Asynchronous | FileOptions.WriteThrough
        );
        await stream.WriteAsync(bytes, cancellationToken);
        await stream.FlushAsync(cancellationToken);
        stream.Flush(flushToDisk: true);
    }
}
