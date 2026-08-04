namespace ChatPilot.Api.FrontendActions;

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = true)]
internal sealed class FeatureGateAttribute(string featureKey) : Attribute
{
    public string FeatureKey { get; } = featureKey;
}
