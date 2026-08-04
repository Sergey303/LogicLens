using System.Xml;
using System.Xml.Linq;

namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml;

public static class OoxmlXml
{
    public static XDocument Parse(OoxmlPart part, long maxCharacters = 8_388_608)
    {
        ArgumentNullException.ThrowIfNull(part);
        using var stream = new MemoryStream(part.Content, writable: false);
        using var reader = XmlReader.Create(stream, new XmlReaderSettings
        {
            DtdProcessing = DtdProcessing.Prohibit,
            XmlResolver = null,
            MaxCharactersInDocument = maxCharacters,
            IgnoreComments = true,
            IgnoreProcessingInstructions = true,
        });
        try
        {
            return XDocument.Load(reader, LoadOptions.None);
        }
        catch (XmlException exception)
        {
            throw new InvalidDataException($"Malformed OOXML XML part: {part.Name}", exception);
        }
    }
}
