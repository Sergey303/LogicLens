namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class ProtectedRevisionBytesContractTests
{
    public static async Task DenialStopsBeforeMetadataLookupAsync()
    {
        var fixture = new ProtectedReadFixture(deny: true, revoked: false);
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync());
        Assert(fixture.Events.SequenceEqual(["access"]), "Denied read must not reveal metadata.");
    }

    public static async Task RevocationStopsBeforeObjectLookupAsync()
    {
        var fixture = new ProtectedReadFixture(deny: false, revoked: true);
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync());
        Assert(
            fixture.Events.SequenceEqual(["access", "locator"]),
            "Revoked read must stop before immutable object lookup."
        );
    }

    public static async Task SupersedeStopsBeforeObjectLookupAsync()
    {
        var fixture = new ProtectedReadFixture(deny: false, revoked: false, superseded: true);
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync());
        Assert(
            fixture.Events.SequenceEqual(["access", "locator"]),
            "Superseded read must stop before immutable object lookup."
        );
    }

    public static async Task AuthorizedReadUsesObjectStoreLastAsync()
    {
        var fixture = new ProtectedReadFixture(deny: false, revoked: false);
        await using var stream = await fixture.OpenAsync();
        Assert(stream.Length == 3, "Authorized read must return immutable bytes.");
        Assert(
            fixture.Events.SequenceEqual(["access", "locator", "object"]),
            "Protected read order must be access, metadata, then bytes."
        );
    }

    private static async Task AssertThrowsAsync<T>(Func<Task> action) where T : Exception
    {
        try
        {
            await action();
            throw new InvalidOperationException($"Expected {typeof(T).Name}.");
        }
        catch (T)
        {
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
