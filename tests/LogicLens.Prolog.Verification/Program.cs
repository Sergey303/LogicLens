using System.Text;
using LogicLens.Prolog.Serialization;

namespace LogicLens.Prolog.Verification;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1 || string.IsNullOrWhiteSpace(args[0]))
            {
                throw new ArgumentException(
                    "Expected exactly one output path argument.");
            }

            const string atomValue = "atom'quote\\slash\nline\tend";
            const string stringValue = "string \"quote\" 'apostrophe' \\slash\nline\tend";

            var content =
                ":- module(escaping_generated, [escaped_atom/1, escaped_string/1]).\n\n" +
                $"escaped_atom({PrologText.Atom(atomValue)}).\n" +
                $"escaped_string({PrologText.String(stringValue)}).\n";

            var outputPath = Path.GetFullPath(args[0]);
            Directory.CreateDirectory(
                Path.GetDirectoryName(outputPath)
                ?? throw new InvalidOperationException("Output path has no directory."));
            File.WriteAllText(outputPath, content, new UTF8Encoding(false));

            ExpectRejectedControlCharacter();
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Prolog serialization verification preparation failed.");
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static void ExpectRejectedControlCharacter()
    {
        try
        {
            _ = PrologText.String("unsupported\u0001control");
        }
        catch (ArgumentException)
        {
            return;
        }

        throw new InvalidOperationException(
            "Unsupported control character was not rejected.");
    }
}
