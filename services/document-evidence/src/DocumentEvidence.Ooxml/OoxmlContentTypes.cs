using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlContentTypes
{
    private static readonly XNamespace Types =
        "http://schemas.openxmlformats.org/package/2006/content-types";

    public static void DemandOverride(
        OoxmlPackageSnapshot package,
        string partName,
        string contentType
    )
    {
        var document = OoxmlXml.Parse(package.RequirePart("[Content_Types].xml"));
        var expectedName = $"/{partName}";
        var found = document.Root?
            .Elements(Types + "Override")
            .Any(element =>
                string.Equals(
                    (string?)element.Attribute("PartName"),
                    expectedName,
                    StringComparison.Ordinal
                )
                && string.Equals(
                    (string?)element.Attribute("ContentType"),
                    contentType,
                    StringComparison.Ordinal
                )
            ) == true;
        if (!found)
        {
            throw new InvalidDataException(
                $"OOXML content type is missing for {partName}: {contentType}"
            );
        }
    }
}
