namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
internal sealed class InvalidatesApiEndpointAttribute(Type controllerType, string methodName) : Attribute
{
    public Type ControllerType { get; } = controllerType ?? throw new ArgumentNullException(nameof(controllerType));

    public string MethodName { get; } = string.IsNullOrWhiteSpace(methodName)
        ? throw new ArgumentException("Method name is required.", nameof(methodName))
        : methodName;
}
