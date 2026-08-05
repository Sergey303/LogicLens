using KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class OoxmlSecurityContractTests
{
    private const string OfficeDocumentRelationship =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument";

    public static async Task CanonicalIdentityIgnoresZipOrderAndTimestampAsync()
    {
        var firstBytes = DocxFixture.Build(
            reverse: false,
            timestamp: new DateTimeOffset(2024, 1, 1, 0, 0, 0, TimeSpan.Zero)
        );
        var secondBytes = DocxFixture.Build(
            reverse: true,
            timestamp: new DateTimeOffset(2025, 1, 1, 0, 0, 0, TimeSpan.Zero)
        );
        var first = await ReadAsync(firstBytes);
        var second = await ReadAsync(secondBytes);

        TestAssert.True(
            first.Identity.ArtifactSha256 != second.Identity.ArtifactSha256,
            "Container-level artifact hashes must expose different ZIP bytes."
        );
        TestAssert.Equal(
            first.Identity.EntriesSha256,
            second.Identity.EntriesSha256,
            "Canonical package identity must ignore ZIP ordering and timestamps."
        );
        TestAssert.Equal(
            "Contract fixture",
            first.Identity.CoreProperties.Title,
            "Core-property whitespace must be normalized."
        );
        TestAssert.Equal(
            "2026-08-04T12:00:00.0000000+00:00",
            first.Identity.CoreProperties.CreatedUtc,
            "Core timestamps must be canonical UTC values."
        );
    }

    public static async Task PackageAbsoluteRelationshipIsResolvedAsync()
    {
        var packageBytes = OoxmlTestZip.Build([
            ("[Content_Types].xml", "<Types />"),
            ("word/document.xml", "<document />"),
            ("_rels/.rels", $"""
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                  <Relationship Id="rId1" Type="{OfficeDocumentRelationship}"
                    Target="/word/document.xml" />
                </Relationships>
                """),
        ]);
        var package = await ReadAsync(packageBytes);
        var relationships = OoxmlRelationships.Read(package, "_rels/.rels", "");
        TestAssert.Equal(
            "word/document.xml",
            OoxmlRelationships.DemandSingleTargetByType(
                relationships,
                OfficeDocumentRelationship
            ),
            "Package-absolute internal relationship was not resolved from ZIP root."
        );
    }

    public static async Task TraversalPartIsRejectedAsync()
    {
        var package = OoxmlTestZip.Build([
            ("[Content_Types].xml", "<Types />"),
            ("../escape.xml", "<escape />"),
        ]);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ReadAsync(package),
            "A traversal-like ZIP entry must be rejected."
        );
    }

    public static async Task CaseInsensitiveDuplicatePartIsRejectedAsync()
    {
        var package = OoxmlTestZip.Build([
            ("[Content_Types].xml", "<Types />"),
            ("word/document.xml", "<a />"),
            ("WORD/document.xml", "<b />"),
        ]);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ReadAsync(package),
            "Case-insensitive duplicate OOXML names must fail closed."
        );
    }

    public static async Task PackageAndExpansionLimitsAreEnforcedAsync()
    {
        var package = OoxmlTestZip.Build([
            ("[Content_Types].xml", new string('x', 4_096)),
        ]);
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ReadAsync(package, new OoxmlPackageLimits(MaxPackageBytes: 16)),
            "The compressed package byte limit must be enforced before ZIP parsing."
        );
        await TestAssert.ThrowsAsync<InvalidDataException>(
            () => ReadAsync(package, new OoxmlPackageLimits(MaxUncompressedBytes: 32)),
            "The uncompressed OOXML limit must stop expansion bombs."
        );
    }

    private static Task<OoxmlPackageSnapshot> ReadAsync(
        byte[] content,
        OoxmlPackageLimits? limits = null
    ) => OoxmlPackageReader.ReadAsync(
        new MemoryStream(content, writable: false),
        limits
    );
}
