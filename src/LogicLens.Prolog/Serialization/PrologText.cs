using System.Text;

namespace LogicLens.Prolog.Serialization;

public static class PrologText
{
    public static string Atom(string value) => Quote(value, '\'');

    public static string String(string value) => Quote(value, '"');

    private static string Quote(string value, char quote)
    {
        ArgumentNullException.ThrowIfNull(value);

        var builder = new StringBuilder(value.Length + 2);
        builder.Append(quote);

        foreach (var rune in value.EnumerateRunes())
        {
            switch (rune.Value)
            {
                case '\\':
                    builder.Append("\\\\");
                    break;
                case '\n':
                    builder.Append("\\n");
                    break;
                case '\r':
                    builder.Append("\\r");
                    break;
                case '\t':
                    builder.Append("\\t");
                    break;
                case '\'':
                    if (quote == '\'')
                    {
                        builder.Append("\\'");
                    }
                    else
                    {
                        builder.Append('\'');
                    }

                    break;
                case '"':
                    if (quote == '"')
                    {
                        builder.Append("\\\"");
                    }
                    else
                    {
                        builder.Append('"');
                    }

                    break;
                default:
                    if (rune.Value < 0x20 || rune.Value == 0x7f)
                    {
                        throw new ArgumentException(
                            $"Unsupported control character U+{rune.Value:X4}.",
                            nameof(value));
                    }

                    builder.Append(rune.ToString());
                    break;
            }
        }

        builder.Append(quote);
        return builder.ToString();
    }
}
