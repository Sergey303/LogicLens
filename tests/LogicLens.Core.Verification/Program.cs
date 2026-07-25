using System.Text;
using System.Text.Json;
using LogicLens.Core.Graph;
using LogicLens.Core.Identity;
using LogicLens.Core.Import;
using LogicLens.Core.Model;

namespace LogicLens.Core.Verification;

internal static class Program
{
    private static int Main()
    {
        try
        {
            var repositoryRoot = FindRepositoryRoot();
            VerifyGoldenVectors(repositoryRoot);
            VerifyFixtureImport(repositoryRoot);
            VerifyNormalizationRules();
            VerifyUnsupportedNestedProperty();

            Console.WriteLine("LogicLens.Core verification passed.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("LogicLens.Core verification failed.");
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static void VerifyGoldenVectors(string repositoryRoot)
    {
        var path = Path.Combine(
            repositoryRoot,
            "fixtures",
            "zero-epoch",
            "expected",
            "fact-id-v1-golden.json");

        using var document = JsonDocument.Parse(File.ReadAllText(path));
        var root = document.RootElement;
        Equal(1, root.GetProperty("encodingVersion").GetInt32(), "Encoding version");

        var count = 0;
        foreach (var vector in root.GetProperty("cases").EnumerateArray())
        {
            count++;
            var subject = RequiredString(vector, "subject");
            var predicate = RequiredString(vector, "predicate");
            var value = ReadObject(vector.GetProperty("object"));
            var expectedBytes = RequiredString(vector, "canonicalBytesHex");
            var expectedFactId = RequiredString(vector, "factId");

            Equal(
                expectedBytes,
                FactIdV1.EncodeHex(subject, predicate, value),
                $"Canonical bytes for vector {count}");
            Equal(
                expectedFactId,
                FactIdV1.Compute(subject, predicate, value),
                $"FactId for vector {count}");
        }

        Check(count >= 5, "At least five independent FactId vectors are required.");
    }

    private static void VerifyFixtureImport(string repositoryRoot)
    {
        var fixtureRoot = Path.Combine(repositoryRoot, "fixtures", "zero-epoch");
        var originCatalog = ReadOriginCatalog(
            Path.Combine(fixtureRoot, "expected", "origins.json"));
        var importer = new FogSubsetImporter();
        var graphBuilder = new CanonicalGraphBuilder();

        foreach (var absolutePath in Directory
                     .EnumerateFiles(Path.Combine(fixtureRoot, "archive"), "*.fog")
                     .OrderBy(static path => path, StringComparer.Ordinal))
        {
            var relativePath = Path
                .GetRelativePath(repositoryRoot, absolutePath)
                .Replace('\\', '/');

            using var stream = File.OpenRead(absolutePath);
            var import = importer.Import(
                stream,
                relativePath,
                context => ResolveOrigin(originCatalog, context));

            foreach (var occurrence in import.Occurrences)
            {
                graphBuilder.Add(occurrence.Fact, occurrence.Origin);
            }
        }

        var graph = graphBuilder.Build();
        VerifyExpectedGraph(
            graph,
            Path.Combine(fixtureRoot, "expected", "normalized-facts.json"));
    }

    private static Dictionary<(string SourcePath, string EntityId), Origin> ReadOriginCatalog(
        string path)
    {
        using var document = JsonDocument.Parse(File.ReadAllText(path));
        var result = new Dictionary<(string SourcePath, string EntityId), Origin>();

        foreach (var element in document.RootElement.GetProperty("origins").EnumerateArray())
        {
            var origin = new Origin(
                RequiredString(element, "originId"),
                RequiredString(element, "sourcePath"),
                RequiredString(element, "sourceDbId"),
                RequiredString(element, "entityId"));

            var key = (origin.SourcePath, origin.EntityId);
            Check(result.TryAdd(key, origin), $"Duplicate origin catalog key: {key}.");
        }

        return result;
    }

    private static Origin ResolveOrigin(
        IReadOnlyDictionary<(string SourcePath, string EntityId), Origin> catalog,
        FogOriginContext context)
    {
        var key = (context.SourcePath, context.EntityId);
        if (!catalog.TryGetValue(key, out var origin))
        {
            throw new InvalidOperationException($"Missing origin for {key}.");
        }

        Equal(context.SourceDbId, origin.SourceDbId, $"Source dbid for {key}");
        return origin;
    }

    private static void VerifyExpectedGraph(CanonicalGraph graph, string expectedPath)
    {
        using var document = JsonDocument.Parse(File.ReadAllText(expectedPath));
        var root = document.RootElement;
        var expectedCount = root.GetProperty("factCount").GetInt32();
        Equal(expectedCount, graph.Count, "Canonical graph fact count");

        var actualById = graph.Entries.ToDictionary(
            static entry => entry.Fact.FactId,
            StringComparer.Ordinal);
        var seen = new HashSet<string>(StringComparer.Ordinal);

        foreach (var expected in root.GetProperty("facts").EnumerateArray())
        {
            var expectedFactId = RequiredString(expected, "factId");
            var subject = RequiredString(expected, "subject");
            var predicate = RequiredString(expected, "predicate");
            var value = ReadObject(expected.GetProperty("object"));
            var recomputed = CanonicalFact.Create(subject, predicate, value);

            Equal(expectedFactId, recomputed.FactId, $"Expected FactId {expectedFactId}");
            if (!actualById.TryGetValue(expectedFactId, out var actual))
            {
                throw new InvalidOperationException(
                    $"Expected fact is missing: {expectedFactId}.");
            }

            Equal(subject, actual.Fact.Subject, $"Subject for {expectedFactId}");
            Equal(predicate, actual.Fact.Predicate, $"Predicate for {expectedFactId}");
            Equal(value, actual.Fact.Object, $"Object for {expectedFactId}");

            var expectedOrigins = expected.GetProperty("origins")
                .EnumerateArray()
                .Select(static item => item.GetString()
                    ?? throw new InvalidDataException("Origin ID cannot be null."))
                .OrderBy(static id => id, StringComparer.Ordinal)
                .ToArray();
            var actualOrigins = actual.Origins
                .Select(static origin => origin.OriginId)
                .OrderBy(static id => id, StringComparer.Ordinal)
                .ToArray();

            SequenceEqual(expectedOrigins, actualOrigins, $"Origins for {expectedFactId}");
            seen.Add(expectedFactId);
        }

        Equal(actualById.Count, seen.Count, "No unexpected canonical facts");
    }

    private static void VerifyNormalizationRules()
    {
        const string subject = "urn:test:subject";
        const string predicate = "urn:test:predicate";

        var lower = LiteralObject.LanguageTagged("value", "ru");
        var upper = LiteralObject.LanguageTagged("value", "RU");
        Equal(lower, upper, "Language tags are lower-cased");
        Equal(
            FactIdV1.Compute(subject, predicate, lower),
            FactIdV1.Compute(subject, predicate, upper),
            "Language-tag case does not change FactId");

        var plain = LiteralObject.Plain("value");
        var plainWithSpace = LiteralObject.Plain("value ");
        Check(
            FactIdV1.Compute(subject, predicate, plain)
            != FactIdV1.Compute(subject, predicate, plainWithSpace),
            "Literal lexical whitespace must affect FactId.");

        var graphBuilder = new CanonicalGraphBuilder();
        var fact = CanonicalFact.Create(subject, predicate, plain);
        var origin = new Origin("origin:test", "fixture.fog", "fixture", subject);
        graphBuilder.Add(fact, origin);
        graphBuilder.Add(fact, origin);
        Equal(1, graphBuilder.Build().Count, "Repeated occurrence is deduplicated");
    }

    private static void VerifyUnsupportedNestedProperty()
    {
        const string xml = """
            <?xml version="1.0" encoding="utf-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:o="http://fogid.net/o/"
                     dbid="invalid">
              <o:person rdf:about="urn:test:person">
                <o:name><o:nested>not supported</o:nested></o:name>
              </o:person>
            </rdf:RDF>
            """;

        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(xml));
        var importer = new FogSubsetImporter();

        ExpectThrows<FogImportException>(() => importer.Import(
            stream,
            "invalid.fog",
            context => new Origin(
                "origin:invalid",
                context.SourcePath,
                context.SourceDbId,
                context.EntityId)));
    }

    private static FactObject ReadObject(JsonElement element)
    {
        var kind = RequiredString(element, "kind");
        return kind switch
        {
            "iri" => new IriObject(RequiredString(element, "value")),
            "literal" => ReadLiteral(element),
            _ => throw new InvalidDataException($"Unknown object kind '{kind}'.")
        };
    }

    private static LiteralObject ReadLiteral(JsonElement element)
    {
        var literalKind = RequiredString(element, "literalKind");
        var lexical = RequiredString(element, "lexical", allowEmpty: true);

        return literalKind switch
        {
            "plain" => LiteralObject.Plain(lexical),
            "language" => LiteralObject.LanguageTagged(
                lexical,
                RequiredString(element, "language")),
            "datatype" => LiteralObject.DatatypeTagged(
                lexical,
                RequiredString(element, "datatype")),
            _ => throw new InvalidDataException($"Unknown literal kind '{literalKind}'.")
        };
    }

    private static string RequiredString(
        JsonElement element,
        string propertyName,
        bool allowEmpty = false)
    {
        var value = element.GetProperty(propertyName).GetString()
            ?? throw new InvalidDataException($"'{propertyName}' cannot be null.");

        if (!allowEmpty && string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException($"'{propertyName}' cannot be empty.");
        }

        return value;
    }

    private static string FindRepositoryRoot()
    {
        foreach (var start in new[]
                 {
                     Directory.GetCurrentDirectory(),
                     AppContext.BaseDirectory
                 })
        {
            DirectoryInfo? directory = new(start);
            while (directory is not null)
            {
                if (File.Exists(Path.Combine(directory.FullName, "README.md"))
                    && Directory.Exists(Path.Combine(
                        directory.FullName,
                        "fixtures",
                        "zero-epoch")))
                {
                    return directory.FullName;
                }

                directory = directory.Parent;
            }
        }

        throw new DirectoryNotFoundException(
            "Could not locate the LogicLens repository root.");
    }

    private static void ExpectThrows<TException>(Action action)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException)
        {
            return;
        }

        throw new InvalidOperationException(
            $"Expected exception {typeof(TException).Name} was not thrown.");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void Equal<T>(T expected, T actual, string context)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException(
                $"{context}: expected '{expected}', actual '{actual}'.");
        }
    }

    private static void SequenceEqual<T>(
        IReadOnlyList<T> expected,
        IReadOnlyList<T> actual,
        string context)
    {
        if (!expected.SequenceEqual(actual))
        {
            throw new InvalidOperationException(
                $"{context}: expected [{string.Join(", ", expected)}], " +
                $"actual [{string.Join(", ", actual)}].");
        }
    }
}
