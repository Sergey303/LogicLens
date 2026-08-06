namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class FragmentRevocationContractTests
{
    public static async Task DenialStopsBeforeRevisionMetadataAsync()
    {
        var fixture = new FragmentFacadeFixture();
        fixture.DenyAccess();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.ListAsync());
        Assert(fixture.Events.SequenceEqual(["access"]),
            "Denied fragment access must stop before revision metadata.");
    }

    public static async Task RevocationStopsBeforeFragmentStoreAsync()
    {
        var fixture = new FragmentFacadeFixture();
        fixture.Revoke();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.ListAsync());
        AssertStoppedAfterMetadata(fixture, "Revoked");
    }

    public static async Task SupersedeStopsBeforeFragmentStoreAsync()
    {
        var fixture = new FragmentFacadeFixture();
        fixture.Supersede();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.ListAsync());
        AssertStoppedAfterMetadata(fixture, "Superseded");
    }

    public static async Task CurrentRevisionReturnsFragmentsLastAsync()
    {
        var fixture = new FragmentFacadeFixture();
        var fragments = await fixture.ListAsync();
        Assert(fragments.Count == 1, "Current revision must return its fragments.");
        Assert(
            fixture.Events.SequenceEqual(["access", "locator", "fragments"]),
            "Fragment order must be access, revision metadata, then generated store."
        );
    }

    private static void AssertStoppedAfterMetadata(FragmentFacadeFixture fixture, string label)
    {
        Assert(
            fixture.Events.SequenceEqual(["access", "locator"]),
            $"{label} revision must not reach the fragment store."
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
