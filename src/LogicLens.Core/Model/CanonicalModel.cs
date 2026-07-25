using LogicLens.Core.Identity;

namespace LogicLens.Core.Model;

public abstract record FactObject;

public sealed record IriObject : FactObject
{
    public IriObject(string value)
    {
        Value = Guard.Required(value, nameof(value));
    }

    public string Value { get; }
}

public enum LiteralKind
{
    Plain,
    Language,
    Datatype
}

public sealed record LiteralObject : FactObject
{
    private LiteralObject(
        string lexical,
        LiteralKind kind,
        string? language,
        string? datatype)
    {
        Lexical = lexical ?? throw new ArgumentNullException(nameof(lexical));
        Kind = kind;
        Language = language;
        Datatype = datatype;
    }

    public string Lexical { get; }

    public LiteralKind Kind { get; }

    public string? Language { get; }

    public string? Datatype { get; }

    public static LiteralObject Plain(string lexical) =>
        new(lexical, LiteralKind.Plain, null, null);

    public static LiteralObject LanguageTagged(string lexical, string language)
    {
        var normalizedLanguage = Guard.Required(language, nameof(language)).ToLowerInvariant();
        return new LiteralObject(lexical, LiteralKind.Language, normalizedLanguage, null);
    }

    public static LiteralObject DatatypeTagged(string lexical, string datatype) =>
        new(
            lexical,
            LiteralKind.Datatype,
            null,
            Guard.Required(datatype, nameof(datatype)));
}

public sealed record CanonicalFact
{
    private CanonicalFact(
        string factId,
        string subject,
        string predicate,
        FactObject @object)
    {
        FactId = factId;
        Subject = subject;
        Predicate = predicate;
        Object = @object;
    }

    public string FactId { get; }

    public string Subject { get; }

    public string Predicate { get; }

    public FactObject Object { get; }

    public static CanonicalFact Create(
        string subject,
        string predicate,
        FactObject @object)
    {
        subject = Guard.Required(subject, nameof(subject));
        predicate = Guard.Required(predicate, nameof(predicate));
        ArgumentNullException.ThrowIfNull(@object);

        return new CanonicalFact(
            FactIdV1.Compute(subject, predicate, @object),
            subject,
            predicate,
            @object);
    }
}

public sealed record Origin
{
    public Origin(
        string originId,
        string sourcePath,
        string sourceDbId,
        string entityId)
    {
        OriginId = Guard.Required(originId, nameof(originId));
        SourcePath = Guard.Required(sourcePath, nameof(sourcePath));
        SourceDbId = Guard.Required(sourceDbId, nameof(sourceDbId));
        EntityId = Guard.Required(entityId, nameof(entityId));
    }

    public string OriginId { get; }

    public string SourcePath { get; }

    public string SourceDbId { get; }

    public string EntityId { get; }
}

internal static class Guard
{
    public static string Required(string? value, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value, parameterName);
        return value;
    }
}
