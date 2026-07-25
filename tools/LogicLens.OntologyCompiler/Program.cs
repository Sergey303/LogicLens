namespace LogicLens.OntologyCompiler;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            var options = CompilerOptions.Parse(args);
            var repositoryRoot = options.RepositoryRoot ?? FindRepositoryRoot();
            repositoryRoot = Path.GetFullPath(repositoryRoot);
            var sourcePath = Path.GetFullPath(
                Path.IsPathRooted(options.SourcePath)
                    ? options.SourcePath
                    : Path.Combine(repositoryRoot, options.SourcePath));
            var outputDirectory = Path.GetFullPath(
                Path.IsPathRooted(options.OutputDirectory)
                    ? options.OutputDirectory
                    : Path.Combine(repositoryRoot, options.OutputDirectory));
            var relativeSourcePath = Path
                .GetRelativePath(repositoryRoot, sourcePath)
                .Replace('\\', '/');

            using var stream = File.OpenRead(sourcePath);
            var importer = new OntologySubsetImporter();
            var snapshot = importer.Import(stream, relativeSourcePath);
            var writer = new OntologyPrologWriter();
            var package = writer.Build(snapshot, options.CompilerCommit);
            writer.WriteToDirectory(package, outputDirectory);

            Console.WriteLine("Generated ontology label package.");
            Console.WriteLine($"Terms: {package.TermCount}");
            Console.WriteLine($"Labels: {package.LabelCount}");
            Console.WriteLine($"Priorities: {package.PriorityCount}");
            Console.WriteLine($"Package hash: {package.PackageHash}");
            Console.WriteLine($"Output: {outputDirectory}");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Ontology compilation failed.");
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
                    && File.Exists(Path.Combine(directory.FullName, "data", "Ontology.xml")))
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
        string SourcePath,
        string OutputDirectory,
        string CompilerCommit)
    {
        public static CompilerOptions Parse(string[] args)
        {
            string? repositoryRoot = null;
            var sourcePath = "data/Ontology.xml";
            var outputDirectory = "epochs/epoch-000/ontology";
            string? compilerCommit = null;

            for (var index = 0; index < args.Length; index++)
            {
                var option = args[index];
                var value = option switch
                {
                    "--repository-root" or "--source" or "--output" or "--compiler-commit"
                        => ReadValue(args, ref index, option),
                    _ => throw new ArgumentException($"Unknown option '{option}'.")
                };

                switch (option)
                {
                    case "--repository-root":
                        repositoryRoot = value;
                        break;
                    case "--source":
                        sourcePath = value;
                        break;
                    case "--output":
                        outputDirectory = value;
                        break;
                    case "--compiler-commit":
                        compilerCommit = value;
                        break;
                }
            }

            if (string.IsNullOrWhiteSpace(compilerCommit))
            {
                throw new ArgumentException("--compiler-commit is required.");
            }

            return new CompilerOptions(
                repositoryRoot,
                sourcePath,
                outputDirectory,
                compilerCommit);
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
