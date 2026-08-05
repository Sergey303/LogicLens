using System.Text;
using KnowledgePilot.LogicLens.DocumentEvidence.Pdf;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Pdf.ContractTests;

internal static class PdfValidationContractTests
{
    public static async Task InvalidSignatureStopsBeforePopplerAsync()
    {
        var runner = new FakePdfProcessRunner();
        var adapter = new PdfPopplerAdapter(runner);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => adapter.ExtractAsync(
                new MemoryStream(Encoding.UTF8.GetBytes("not-a-pdf")),
                Request(1024)
            ),
            "Invalid signature unexpectedly reached Poppler."
        );
        TestAssert.Equal(0, runner.Calls.Count, "Poppler ran before signature validation.");
    }

    public static async Task OversizedInputStopsBeforePopplerAsync()
    {
        var runner = new FakePdfProcessRunner();
        var adapter = new PdfPopplerAdapter(runner);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => adapter.ExtractAsync(
                new MemoryStream(PdfTestFixture.PdfBytes),
                Request(5)
            ),
            "Oversized PDF unexpectedly reached Poppler."
        );
        TestAssert.Equal(0, runner.Calls.Count, "Poppler ran before byte-limit validation.");
    }

    public static async Task HashMismatchStopsBeforePopplerAsync()
    {
        var runner = new FakePdfProcessRunner();
        var adapter = new PdfPopplerAdapter(runner);
        var request = Request(1024) with { ExpectedSha256 = new string('0', 64) };
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => adapter.ExtractAsync(new MemoryStream(PdfTestFixture.PdfBytes), request),
            "Hash mismatch unexpectedly reached Poppler."
        );
        TestAssert.Equal(0, runner.Calls.Count, "Poppler ran before hash pin validation.");
    }

    private static PdfExtractionRequest Request(long maxBytes)
    {
        return new PdfExtractionRequest(
            "fixture-pdf",
            "https://example.test/fixture.pdf",
            maxBytes
        );
    }
}
