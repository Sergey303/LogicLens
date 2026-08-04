#nullable enable

namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class RestCrudControllerAttribute : Attribute
{
    public RestCrudControllerAttribute()
    {
    }

    public RestCrudControllerAttribute(string errorPrefix)
    {
        ErrorPrefix = errorPrefix;
    }

    public string? ErrorPrefix { get; }
}
