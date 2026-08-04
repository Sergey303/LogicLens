namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Method)]
internal sealed class ApiOperationAttribute(ApiOperationKind kind) : Attribute
{
    public ApiOperationKind Kind { get; } = kind;
}
