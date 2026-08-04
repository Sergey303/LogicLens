using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public sealed record OoxmlRelationship(
    string Id,
    string Type,
    string TargetPart
);

public static class OoxmlRelationships
{
    private static readonly XNamespace Relationships =
        "http://schemas.openxmlformats.org/package/2006/relationships";

    public static IReadOnlyList<OoxmlRelationship> Read(
        OoxmlPackageSnapshot package,
        string relationshipPart,
        string sourcePart
    )
    {
        var document = OoxmlXml.Parse(package.RequirePart(relationshipPart));
        var result = new List<OoxmlRelationship>();
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var element in document.Root?.Elements(Relationships + "Relationship") ?? [])
        {
            var id = DemandAttribute(element, "Id");
            var type = DemandAttribute(element, "Type");
            var target = DemandAttribute(element, "Target");
            if (!ids.Add(id))
            {
                throw new InvalidDataException($"Duplicate OOXML relationship ID: {id}");
            }
            if (string.Equals(
                (string?)element.Attribute("TargetMode"),
                "External",
                StringComparison.OrdinalIgnoreCase
            ))
            {
                throw new InvalidDataException($"External OOXML relationship is not trusted: {id}");
            }
            result.Add(new OoxmlRelationship(
                id,
                type,
                OoxmlPathPolicy.ResolveInternalTarget(sourcePart, target)
            ));
        }
        return result;
    }

    public static string DemandSingleTargetByType(
        IReadOnlyList<OoxmlRelationship> relationships,
        string type
    )
    {
        var matches = relationships
            .Where(item => string.Equals(item.Type, type, StringComparison.Ordinal))
            .ToArray();
        return matches.Length == 1
            ? matches[0].TargetPart
            : throw new InvalidDataException($"Expected one OOXML relationship of type: {type}");
    }

    private static string DemandAttribute(XElement element, string name)
    {
        var value = ((string?)element.Attribute(name))?.Trim();
        return string.IsNullOrWhiteSpace(value)
            ? throw new InvalidDataException($"OOXML relationship attribute is missing: {name}")
            : value;
    }
}
