using LogicLens.Core.Graph;
using LogicLens.Core.Import;
using LogicLens.Prolog.Epoch;

namespace LogicLens.EpochCompiler;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            var options = CompilerOptions.Parse(args);
            var repositoryRoot = options.RepositoryRoot ?? FindRepositoryRoot();
            repositoryRoot = Path.GetFullPath(repositoryRoot);
            var fixtureRoot = Path.Combine(repositoryRoot, "fixtures", "zero-epoch");
            var originCatalog = OriginCatalog.LoadJson(Path.Combine(
                fixtureRoot,
                "expected",
                "origins.json"));

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
                var imported = importer.Import(
                    stream,
                    relativePath,
                    originCatalog.Resolve);

                foreach (var occurrence in imported.Occurrences)
                {
                    graphBuilder.Add(occurrence.Fact, occurrence.Origin);
                }
            }

            var graph = graphBuilder.Build();
            var writer = new PrologEpochWriter();
            var package = writer.Build(graph, options.Epoch, options.CompilerCommit);
            var outputDirectory = Path.GetFullPath(
                Path.IsPathRooted(options.OutputDirectory)
                    ? options.OutputDirectory
                    : Path.Combine(repositoryRoot, options.OutputDirectory));
            writer.WriteToDirectory(package, outputDirectory);

            Console.WriteLine($"Generated epoch {package.Epoch} data.");
            Console.WriteLine($"Facts: {package.FactCount}");
            Console.WriteLine($"Origins: {package.OriginCount}");
            Console.WriteLine($"Data hash: {package.DataHash}");
            Console.WriteLine($"Output: {outputDirectory}");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Epoch compilation failed.");
            Console.Error.WriteLine(exception.Message);
            return 1;
        }
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
            "Could not locate the LogicLens repository root. " +
            "Use --repository-root to specify it explicitly.");
    }

    private sealed record CompilerOptions(
        string? RepositoryRoot,
        string OutputDirectory,
        string CompilerCommit,
        int Epoch)
    {
        public static CompilerOptions Parse(string[] args)
        {
            string? repositoryRoot = null;
            var outputDirectory = "epochs/epoch-000";
            string? compilerCommit = null;
            var epoch = 0;

            for (var index = 0; index < args.Length; index++)
            {
                var option = args[index];
                var value = option switch
                {
                    "--repository-root" or "--output" or "--compiler-commit" or "--epoch"
                        => ReadValue(args, ref index, option),
                    _ => throw new ArgumentException($"Unknown option '{option}'.")
                };

                switch (option)
                {
                    case "--repository-root":
                        repositoryRoot = value;
                        break;
                    case "--output":
                        outputDirectory = value;
                        break;
                    case "--compiler-commit":
                        compilerCommit = value;
                        break;
                    case "--epoch":
                        if (!int.TryParse(value, out epoch) || epoch < 0)
                        {
                            throw new ArgumentException(
                                $"Invalid non-negative epoch number '{value}'.");
                        }

                        break;
                }
            }

            if (string.IsNullOrWhiteSpace(compilerCommit))
            {
                throw new ArgumentException("--compiler-commit is required.");
            }

            return new CompilerOptions(
                repositoryRoot,
                outputDirectory,
                compilerCommit,
                epoch);
        }

        private static string ReadValue(
            IReadOnlyList<string> args,
            ref int index,
            string option)
        {
            index++;
            if (index >= args.Count || string.IsNullOrWhiteSpace(args[index]))
            {
                throw new ArgumentException($"Option '{option}' requires a value.");
            }

            return args[index];
        }
    }
}
