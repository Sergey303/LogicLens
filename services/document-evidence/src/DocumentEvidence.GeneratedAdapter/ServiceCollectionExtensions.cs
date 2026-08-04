using System.Net.Http.Headers;
using KnowledgePilot.LogicLens.DocumentEvidence.Application.Ports;
using Microsoft.Extensions.DependencyInjection;

namespace KnowledgePilot.LogicLens.DocumentEvidence.GeneratedAdapter;

public static class ServiceCollectionExtensions
{
    public static IHttpClientBuilder AddAppForgeGeneratedOperationalStore(
        this IServiceCollection services,
        Uri baseAddress
    )
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(baseAddress);
        if (!baseAddress.IsAbsoluteUri)
        {
            throw new ArgumentException("Generated API base address must be absolute.", nameof(baseAddress));
        }
        if (baseAddress.Scheme != Uri.UriSchemeHttp && baseAddress.Scheme != Uri.UriSchemeHttps)
        {
            throw new ArgumentException("Generated API must use HTTP or HTTPS.", nameof(baseAddress));
        }

        return services.AddHttpClient<IGeneratedOperationalStore, AppForgeGeneratedOperationalStore>(
            client =>
            {
                client.BaseAddress = baseAddress;
                client.DefaultRequestHeaders.Accept.Add(
                    new MediaTypeWithQualityHeaderValue("application/json")
                );
            }
        );
    }
}
