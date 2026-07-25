using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace LogicLens.Api.Runtime;

public sealed record PrologCliOptions
{
    public string ExecutablePath { get; init; } = "swipl";

    public string EpochPath { get; init; } = "epochs/epoch-000";

    public int Epoch { get; init; }

    public int Revision { get; init; }

    public int TimeoutMs { get; init; } = 10_000;

    public int MaxOutputBytes { get; init; } = 2_500_000;

    public int MaxErrorBytes { get; init; } = 16_384;
}

public sealed class PrologCliException(
    string code,
    string message,
    Exception? innerException = null)
    : Exception(message, innerException)
{
    public string Code { get; } = code;
}

public interface IPrologCliClient
{
    Task<JsonObject> ExecuteAsync(
        string command,
        JsonObject commandOptions,
        CancellationToken cancellationToken);
}

public sealed class PrologCliClient(PrologCliOptions options)
    : IPrologCliClient
{
    private static readonly HashSet<string> Commands =
        new(StringComparer.Ordinal)
        {
            "health",
            "inspect-facts",
            "entity-view",
            "subgraph"
        };

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = false
    };

    public async Task<JsonObject> ExecuteAsync(
        string command,
        JsonObject commandOptions,
        CancellationToken cancellationToken)
    {
        if (!Commands.Contains(command))
        {
            throw new ArgumentOutOfRangeException(
                nameof(command),
                command,
                "Command is not in the closed API allow-list.");
        }
        ArgumentNullException.ThrowIfNull(commandOptions);
        ValidateOptions();

        var epochPath = Path.GetFullPath(options.EpochPath);
        var entryPath = Path.Combine(epochPath, "entry.pl");
        if (!File.Exists(entryPath))
        {
            throw new PrologCliException(
                "epoch_missing",
                "The configured active epoch entry point is unavailable.");
        }

        var request = new JsonObject
        {
            ["protocolVersion"] = "0.1",
            ["requestId"] = "api-" + command,
            ["command"] = command,
            ["epoch"] = options.Epoch,
            ["revision"] = options.Revision,
            ["options"] = commandOptions.DeepClone()
        };

        var startInfo = new ProcessStartInfo
        {
            FileName = options.ExecutablePath,
            WorkingDirectory = epochPath,
            UseShellExecute = false,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardInputEncoding = new UTF8Encoding(false),
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };
        startInfo.ArgumentList.Add("-q");
        startInfo.ArgumentList.Add("-s");
        startInfo.ArgumentList.Add(entryPath);
        startInfo.ArgumentList.Add("--");

        using var process = new Process { StartInfo = startInfo };
        try
        {
            if (!process.Start())
            {
                throw new PrologCliException(
                    "process_start_failed",
                    "The Prolog runtime did not start.");
            }
        }
        catch (PrologCliException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is InvalidOperationException
                or System.ComponentModel.Win32Exception)
        {
            throw new PrologCliException(
                "process_start_failed",
                "The Prolog runtime could not be started.",
                exception);
        }

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(options.TimeoutMs);

        try
        {
            await process.StandardInput.WriteAsync(
                request.ToJsonString(JsonOptions).AsMemory(),
                timeout.Token);
            await process.StandardInput.WriteLineAsync();
            process.StandardInput.Close();

            var stdoutTask = ReadBoundedAsync(
                process.StandardOutput.BaseStream,
                options.MaxOutputBytes,
                timeout.Token);
            var stderrTask = ReadBoundedAsync(
                process.StandardError.BaseStream,
                options.MaxErrorBytes,
                timeout.Token);

            await process.WaitForExitAsync(timeout.Token);
            var stdout = await stdoutTask;
            _ = await stderrTask;

            var response = ParseResponse(stdout);
            var status = RequiredString(response, "status");
            if (process.ExitCode != 0 || status == "error")
            {
                throw StructuredError(response);
            }
            if (!StringComparer.Ordinal.Equals(status, "ok"))
            {
                throw new PrologCliException(
                    "invalid_response",
                    "The Prolog runtime returned an unknown response status.");
            }

            return response;
        }
        catch (OperationCanceledException exception)
            when (!cancellationToken.IsCancellationRequested)
        {
            Kill(process);
            throw new PrologCliException(
                "timeout",
                "The Prolog runtime exceeded the external API time limit.",
                exception);
        }
        catch (OutputLimitException exception)
        {
            Kill(process);
            throw new PrologCliException(
                "output_limit",
                "The Prolog runtime exceeded the external API output limit.",
                exception);
        }
        finally
        {
            if (!process.HasExited)
            {
                Kill(process);
            }
        }
    }

    private void ValidateOptions()
    {
        if (options.TimeoutMs <= 0
            || options.MaxOutputBytes <= 0
            || options.MaxErrorBytes <= 0
            || options.Epoch < 0
            || options.Revision < 0)
        {
            throw new InvalidOperationException(
                "Prolog CLI options contain an invalid non-positive limit or state.");
        }
    }

    private static JsonObject ParseResponse(byte[] bytes)
    {
        try
        {
            return JsonNode.Parse(Encoding.UTF8.GetString(bytes)) as JsonObject
                ?? throw new PrologCliException(
                    "invalid_response",
                    "The Prolog runtime response is not a JSON object.");
        }
        catch (JsonException exception)
        {
            throw new PrologCliException(
                "invalid_response",
                "The Prolog runtime response is not valid JSON.",
                exception);
        }
    }

    private static PrologCliException StructuredError(JsonObject response)
    {
        if (response["error"] is not JsonObject error)
        {
            return new PrologCliException(
                "process_failed",
                "The Prolog runtime failed without a structured error.");
        }

        var code = OptionalString(error, "code") ?? "process_failed";
        var message = OptionalString(error, "message")
            ?? "The Prolog runtime rejected the command.";
        return new PrologCliException(code, message);
    }

    private static async Task<byte[]> ReadBoundedAsync(
        Stream stream,
        int limit,
        CancellationToken cancellationToken)
    {
        using var output = new MemoryStream(Math.Min(limit, 64 * 1024));
        var buffer = new byte[8192];
        var exceeded = false;
        while (true)
        {
            var read = await stream.ReadAsync(buffer, cancellationToken);
            if (read == 0)
            {
                break;
            }

            if (output.Length + read <= limit)
            {
                output.Write(buffer, 0, read);
            }
            else
            {
                exceeded = true;
            }
        }

        if (exceeded)
        {
            throw new OutputLimitException();
        }
        return output.ToArray();
    }

    private static void Kill(Process process)
    {
        try
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }
        }
        catch (InvalidOperationException)
        {
        }
    }

    private static string RequiredString(JsonObject value, string name) =>
        OptionalString(value, name)
        ?? throw new PrologCliException(
            "invalid_response",
            $"The Prolog runtime response is missing '{name}'.");

    private static string? OptionalString(JsonObject value, string name) =>
        value[name]?.GetValue<string?>();

    private sealed class OutputLimitException : Exception;
}
