using System.Text.Json;
using LogicLens.Protocol.Identity;

namespace LogicLens.Protocol.Verification;

internal static class Program
{
    private static int Main()
    {
        try
        {
            var repositoryRoot = FindRepositoryRoot();
            var path = Path.Combine(
                repositoryRoot,
                "fixtures",
                "zero-epoch",
                "expected",
                "occurrence-id-v1-golden.json");

            using var document = JsonDocument.Parse(File.ReadAllText(path));
            var root = document.RootElement;
            Equal(1, root.GetProperty("encodingVersion").GetInt32(), "Encoding version");

            var count = 0;
            foreach (var vector in root.GetProperty("cases").EnumerateArray())
            {
                count++;
                var name = RequiredString(vector, "name");
                var rootId = RequiredString(vector, "root");
                var steps = vector.GetProperty("steps")
                    .EnumerateArray()
                    .Select(ReadStep)
                    .ToArray();

                Equal(
                    RequiredString(vector, "canonicalBytesHex"),
                    OccurrenceIdV1.EncodeHex(rootId, steps),
                    $"Canonical bytes for {name}");
                Equal(
                    RequiredString(vector, "occurrenceId"),
                    OccurrenceIdV1.Compute(rootId, steps),
                    $"OccurrenceId for {name}");
            }

            Equal(5, count, "Golden vector count");
            ExpectThrows<ArgumentOutOfRangeException>(() => OccurrenceIdV1.Encode(
                "urn:test:root",
                [new OccurrenceStep("f:sha256:test", (OccurrenceDirection)0xff)]));

            Console.WriteLine("LogicLens.Protocol verification passed.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("LogicLens.Protocol verification failed.");
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static OccurrenceStep ReadStep(JsonElement element)
    {
        var direction = RequiredString(element, "direction") switch
        {
            "outgoing" => OccurrenceDirection.Outgoing,
            "incoming" => OccurrenceDirection.Incoming,
            var value => throw new InvalidDataException(
                $"Unsupported occurrence direction '{value}'.")
        };

        return new OccurrenceStep(
            RequiredString(element, "factId"),
            direction);
    }

    private static string RequiredString(JsonElement element, string propertyName)
    {
        var value = element.GetProperty(propertyName).GetString();
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException(
                $"'{propertyName}' cannot be null, empty, or whitespace.");
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
                    && File.Exists(Path.Combine(
                        directory.FullName,
                        "fixtures",
                        "zero-epoch",
                        "expected",
                        "occurrence-id-v1-golden.json")))
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

    private static void Equal<T>(T expected, T actual, string context)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException(
                $"{context}: expected '{expected}', actual '{actual}'.");
        }
    }
}
