namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class Program
{
    public static async Task<int> Main()
    {
        await OoxmlSecurityContractTests.CanonicalIdentityIgnoresZipOrderAndTimestampAsync();
        await OoxmlSecurityContractTests.PackageAbsoluteRelationshipIsResolvedAsync();
        await OoxmlSecurityContractTests.TraversalPartIsRejectedAsync();
        await OoxmlSecurityContractTests.CaseInsensitiveDuplicatePartIsRejectedAsync();
        await OoxmlSecurityContractTests.PackageAndExpansionLimitsAreEnforcedAsync();
        await DocxContractTests.ParagraphSectionAndTableAnchorsAreStableAsync();
        await DocxContractTests.MissingMainDocumentFailsClosedAsync();
        await XlsxContractTests.WorkbookAnchorsAndValuesAreStableAsync();
        await XlsxContractTests.ExternalWorksheetRelationshipFailsClosedAsync();
        await XlsxContractTests.UnsupportedCellTypeFailsClosedAsync();
        await OoxmlCompletionContractTests.DocxCompletionUsesSemanticFragmentIdentityAsync();
        await OoxmlCompletionContractTests.XlsxCompletionRetainsFormulaProvenanceAsync();
        await EngDocFixtureContractTests.CommittedEngDocXlsxIsParsedAsync();
        Console.WriteLine("Document Evidence OOXML adapter contract tests passed.");
        return 0;
    }
}
