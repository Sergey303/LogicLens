namespace KnowledgePilot.LogicLens.DocumentEvidence.Ooxml.ContractTests;

internal static class TestAssert
{
    public static void True(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    public static void Equal<T>(T expected, T actual, string message)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException(
                $"{message} Expected: {expected}; actual: {actual}."
            );
        }
    }

    public static async Task ThrowsAsync<T>(Func<Task> action, string message)
        where T : Exception
    {
        try
        {
            await action();
        }
        catch (T)
        {
            return;
        }
        throw new InvalidOperationException(message);
    }
}
