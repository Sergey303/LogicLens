namespace LogicLens.State;

internal static class JsonDocument
{
    public static System.Text.Json.JsonDocument Parse(ReadOnlySpan<byte> utf8Json) =>
        System.Text.Json.JsonDocument.Parse(utf8Json.ToArray());
}
