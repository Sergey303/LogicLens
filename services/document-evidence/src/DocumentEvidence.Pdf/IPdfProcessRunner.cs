namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

public interface IPdfProcessRunner
{
    Task<PdfProcessResult> RunAsync(
        string executable,
        IReadOnlyList<string> arguments,
        string workingDirectory,
        CancellationToken cancellationToken
    );
}

public sealed record PdfProcessResult(
    int ExitCode,
    string StandardOutput,
    string StandardError
);
