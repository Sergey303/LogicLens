using LogicLens.Core.Model;

namespace LogicLens.Core.Graph;

public sealed record CanonicalFactEntry(
    CanonicalFact Fact,
    IReadOnlyList<Origin> Origins);

public sealed class CanonicalGraph
{
    internal CanonicalGraph(IReadOnlyList<CanonicalFactEntry> entries)
    {
        Entries = entries;
    }

    public IReadOnlyList<CanonicalFactEntry> Entries { get; }

    public int Count => Entries.Count;
}

public sealed class CanonicalGraphBuilder
{
    private readonly Dictionary<string, MutableEntry> _entries =
        new(StringComparer.Ordinal);

    public void Add(CanonicalFact fact, Origin origin)
    {
        ArgumentNullException.ThrowIfNull(fact);
        ArgumentNullException.ThrowIfNull(origin);

        if (!_entries.TryGetValue(fact.FactId, out var existing))
        {
            existing = new MutableEntry(fact);
            _entries.Add(fact.FactId, existing);
        }
        else if (!SameTriple(existing.Fact, fact))
        {
            throw new InvalidOperationException(
                $"FactId collision detected for '{fact.FactId}'.");
        }

        if (!StringComparer.Ordinal.Equals(origin.EntityId, fact.Subject))
        {
            throw new InvalidOperationException(
                $"Origin '{origin.OriginId}' belongs to '{origin.EntityId}', " +
                $"but the fact subject is '{fact.Subject}'.");
        }

        if (existing.Origins.TryGetValue(origin.OriginId, out var previousOrigin))
        {
            if (previousOrigin != origin)
            {
                throw new InvalidOperationException(
                    $"OriginId '{origin.OriginId}' identifies different origin metadata.");
            }

            return;
        }

        existing.Origins.Add(origin.OriginId, origin);
    }

    public CanonicalGraph Build()
    {
        var entries = _entries.Values
            .OrderBy(static entry => entry.Fact.FactId, StringComparer.Ordinal)
            .Select(static entry => new CanonicalFactEntry(
                entry.Fact,
                entry.Origins.Values
                    .OrderBy(static origin => origin.OriginId, StringComparer.Ordinal)
                    .ToArray()))
            .ToArray();

        return new CanonicalGraph(entries);
    }

    private static bool SameTriple(CanonicalFact left, CanonicalFact right) =>
        StringComparer.Ordinal.Equals(left.Subject, right.Subject)
        && StringComparer.Ordinal.Equals(left.Predicate, right.Predicate)
        && Equals(left.Object, right.Object);

    private sealed class MutableEntry
    {
        public MutableEntry(CanonicalFact fact)
        {
            Fact = fact;
        }

        public CanonicalFact Fact { get; }

        public SortedDictionary<string, Origin> Origins { get; } =
            new(StringComparer.Ordinal);
    }
}
