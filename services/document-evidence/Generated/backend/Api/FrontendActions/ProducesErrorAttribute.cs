namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
internal sealed class ProducesErrorAttribute(string errorCode) : Attribute
{
    public string ErrorCode { get; } = errorCode ?? throw new ArgumentNullException(nameof(errorCode));
}
