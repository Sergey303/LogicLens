using KnowledgePilot.LogicLens.DocumentEvidence.Xlsx;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class EngDocFixtureContractTests
{
    private const string XlsxArtifactSha256 =
        "61550775c9466c711781ee2555e9b3c9a3871471c2b3d28588d4d183474bde9c";

    public static async Task CommittedEngDocXlsxIsParsedAsync()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory,
            "fixtures",
            "engdoc-confirmed-package-checklist.xlsx"
        );
        await using var stream = File.OpenRead(path);
        var workbook = await new XlsxAdapter().ExtractAsync(stream);

        TestAssert.Equal(
            XlsxArtifactSha256,
            workbook.ArtifactSha256,
            "Committed EngDoc XLSX bytes do not match its accepted manifest."
        );
        TestAssert.Equal(1, workbook.Sheets.Count, "EngDoc workbook sheet count changed.");
        TestAssert.Equal(
            "Package Check",
            workbook.Sheets[0].Name,
            "EngDoc workbook sheet name changed."
        );
        TestAssert.True(
            workbook.Sheets[0].Cells.Count >= 40,
            "EngDoc workbook produced too few canonical cells."
        );
        var values = workbook.Sheets[0].Cells
            .Select(cell => cell.DisplayValue)
            .Where(value => value is not null)
            .ToHashSet(StringComparer.Ordinal);
        foreach (var expected in new[]
        {
            "confirmed-power-conflict",
            "Confirmed",
            "120 W",
            "100 W",
        })
        {
            TestAssert.True(
                values.Contains(expected),
                $"EngDoc workbook value was not retained: {expected}"
            );
        }
        TestAssert.Equal(
            "EngDoc Sentinel",
            workbook.CoreProperties.Creator,
            "EngDoc workbook creator provenance was not retained."
        );
    }
}
