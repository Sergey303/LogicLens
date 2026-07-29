using System.Text.Json.Nodes;

namespace LogicLens.Api.Runtime;

public sealed class StateCheckingPrologCliClient(
    PrologCliClient inner,
    PrologCliOptions expected)
    : IPrologCliClient
{
    public async Task<JsonObject> ExecuteAsync(
        string command,
        JsonObject commandOptions,
        CancellationToken cancellationToken)
    {
        var response = await inner.ExecuteAsync(
            command,
            commandOptions,
            cancellationToken);
        var epoch = RequiredInt(response, "epoch");
        var revision = RequiredInt(response, "revision");
        if (epoch != expected.Epoch || revision != expected.Revision)
        {
            throw new PrologCliException(
                "state_mismatch",
                "The logical runtime response differs from the selected transactional state.");
        }
        return response;
    }

    private static int RequiredInt(JsonObject value, string name)
    {
        try
        {
            return value[name]?.GetValue<int>()
                ?? throw new PrologCliException(
                    "invalid_response",
                    $"The Prolog runtime response is missing integer '{name}'.");
        }
        catch (InvalidOperationException exception)
        {
            throw new PrologCliException(
                "invalid_response",
                $"The Prolog runtime response field '{name}' is not an integer.",
                exception);
        }
    }
}
