namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = true)]
internal sealed class PolicyGateAttribute(string policyKey) : Attribute
{
    public string PolicyKey { get; } = policyKey;
}
