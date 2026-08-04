import type { QueryClient } from "@tanstack/react-query";

export interface EndpointKeyResolver {
  resolveAffectedEndpointKeys(realtimeKey: string): readonly string[];
}

export async function invalidateEndpointKeys(
  queryClient: QueryClient,
  endpointKeys: readonly string[],
): Promise<void> {
  if (endpointKeys.length === 0) {
    return;
  }

  const endpointKeySet = new Set(endpointKeys);
  await queryClient.invalidateQueries({
    predicate: (query) => {
      const firstPart = query.queryKey[0];
      return typeof firstPart === "string" && endpointKeySet.has(firstPart);
    },
  });
}

export async function invalidateResolvedEndpointKeys(
  queryClient: QueryClient,
  resolver: EndpointKeyResolver,
  realtimeKey: string,
): Promise<void> {
  await invalidateEndpointKeys(queryClient, resolver.resolveAffectedEndpointKeys(realtimeKey));
}
