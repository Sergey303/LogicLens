namespace KnowledgePilot.LogicLens.DocumentEvidence.Application.ContractTests;

internal static class RevisionReadPlanContractTests
{
    public static async Task IssueAuthorizesBeforeMetadataAndNeverReadsBytesAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        Assert(plan.RevisionNumber == 1, "Issued plan must bind the revision number.");
        Assert(
            fixture.Events.SequenceEqual(["access", "locator"]),
            "Issuance must authorize before metadata and must not open bytes."
        );
    }

    public static async Task ExecutionReauthorizesBeforeMetadataAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        fixture.DenyAccess();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync(plan));
        Assert(fixture.Events.SequenceEqual(["access"]), "Denied execution must not read metadata.");
    }

    public static async Task RevocationAfterIssuanceStopsBeforeBytesAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        fixture.Revoke();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync(plan));
        AssertStoppedAfterMetadata(fixture, "Revoked");
    }

    public static async Task SupersedeAfterIssuanceStopsBeforeBytesAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        fixture.Supersede();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync(plan));
        AssertStoppedAfterMetadata(fixture, "Superseded");
    }

    public static async Task ChangedObjectIdentityInvalidatesPlanAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        fixture.ChangeObjectHash();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync(plan));
        AssertStoppedAfterMetadata(fixture, "Stale");
    }

    public static async Task ExpiredPlanStopsBeforeAuthorizationAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        fixture.Expire();
        await AssertThrowsAsync<UnauthorizedAccessException>(() => fixture.OpenAsync(plan));
        Assert(fixture.Events.Count == 0, "Expired plans must stop before access and metadata calls.");
    }

    public static async Task ValidPlanOpensImmutableBytesLastAsync()
    {
        var fixture = new RevisionReadPlanFixture();
        var plan = await fixture.IssueAsync();
        fixture.ClearEvents();
        await using var stream = await fixture.OpenAsync(plan);
        Assert(stream.Length == 3, "Valid read plan must return immutable bytes.");
        Assert(
            fixture.Events.SequenceEqual(["access", "locator", "object"]),
            "Execution order must be access, metadata, then object bytes."
        );
    }

    private static void AssertStoppedAfterMetadata(RevisionReadPlanFixture fixture, string label)
    {
        Assert(
            fixture.Events.SequenceEqual(["access", "locator"]),
            $"{label} plan must stop before immutable object lookup."
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
