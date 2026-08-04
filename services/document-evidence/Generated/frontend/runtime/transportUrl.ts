import { TransportRuntimeError } from "./transportErrors";
import type { EndpointTransportBindingMetadata, ResolvedTransportInput } from "./transportTypes";
import { appendWireValues, toWireString } from "./transportWireValues";

export function buildUrl(
  metadata: EndpointTransportBindingMetadata,
  resolvedInputs: readonly ResolvedTransportInput[],
): string {
  const routeBindings = resolvedInputs.filter((entry) => entry.metadata.bindingSource === "route");
  const queryBindings = resolvedInputs.filter((entry) => entry.metadata.bindingSource === "query");
  const routeValueMap = new Map<string, string>();

  for (const entry of routeBindings) {
    if (entry.value === undefined || entry.value === null) {
      continue;
    }

    const encodedValue = encodeURIComponent(
      toWireString(entry.value, "route input", metadata.endpointKey, entry.metadata.inputKey),
    );
    setRouteValue(routeValueMap, entry.metadata.inputKey, encodedValue);
    setRouteValue(routeValueMap, entry.metadata.name, encodedValue);
    setRouteValue(routeValueMap, entry.metadata.wireName, encodedValue);
  }

  const route = replaceRouteTokens(metadata, routeValueMap);
  const query = buildQueryString(queryBindings, metadata.endpointKey);

  if (!query) {
    return route;
  }

  return route.includes("?") ? `${route}&${query}` : `${route}?${query}`;
}

function replaceRouteTokens(
  metadata: EndpointTransportBindingMetadata,
  routeValueMap: Map<string, string>,
): string {
  const unresolvedPlaceholders: string[] = [];

  const route = metadata.routeTemplate.replace(/\{([^}]+)\}/g, (full, tokenRaw: string) => {
    const routeToken = normalizeRouteToken(tokenRaw);
    const resolved = getRouteValue(routeValueMap, routeToken);
    if (resolved === undefined) {
      unresolvedPlaceholders.push(tokenRaw);
      return full;
    }
    return resolved;
  });

  if (unresolvedPlaceholders.length > 0) {
    throw new TransportRuntimeError(
      `[transportRuntime] Missing route values for endpoint '${metadata.endpointKey}': ${unresolvedPlaceholders.join(", ")}.`,
    );
  }

  return route;
}

function buildQueryString(
  queryBindings: readonly ResolvedTransportInput[],
  endpointKey: string,
): string {
  const params = new URLSearchParams();

  for (const entry of queryBindings) {
    appendQueryInput(entry, params, endpointKey);
  }

  return params.toString();
}

function appendQueryInput(
  entry: ResolvedTransportInput,
  params: URLSearchParams,
  endpointKey: string,
): void {
  if (isPlainQueryObject(entry.value)) {
    appendQueryObject(entry.value, "", params, endpointKey, entry.metadata.inputKey);
    return;
  }

  appendWireValues(
    entry.value,
    entry.metadata.required,
    entry.metadata.nullable,
    (value) => params.append(entry.metadata.wireName, value),
    endpointKey,
    entry.metadata.inputKey,
    "query input",
  );
}

function appendQueryObject(
  value: Record<string, unknown>,
  prefix: string,
  params: URLSearchParams,
  endpointKey: string,
  inputKey: string,
): void {
  for (const [key, child] of Object.entries(value)) {
    if (child === undefined || child === null || child === "") {
      continue;
    }

    const nextPrefix = prefix ? `${prefix}.${key}` : key;
    appendNestedQueryValue(child, nextPrefix, params, endpointKey, inputKey);
  }
}

function appendNestedQueryValue(
  value: unknown,
  key: string,
  params: URLSearchParams,
  endpointKey: string,
  inputKey: string,
): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      const itemKey = `${key}[${index}]`;
      appendNestedQueryValue(item, itemKey, params, endpointKey, inputKey);
    });
    return;
  }

  if (isPlainQueryObject(value)) {
    appendQueryObject(value, key, params, endpointKey, inputKey);
    return;
  }

  params.append(key, toWireString(value, "query input", endpointKey, inputKey));
}

function isPlainQueryObject(value: unknown): value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }

  if (value instanceof Date || value instanceof FormData || value instanceof URLSearchParams) {
    return false;
  }

  if (typeof Blob !== "undefined" && value instanceof Blob) {
    return false;
  }

  return true;
}

function setRouteValue(routeValueMap: Map<string, string>, key: string, value: string): void {
  routeValueMap.set(key, value);
  routeValueMap.set(key.toLowerCase(), value);
}

function getRouteValue(routeValueMap: Map<string, string>, key: string): string | undefined {
  return routeValueMap.get(key) ?? routeValueMap.get(key.toLowerCase());
}

function normalizeRouteToken(tokenRaw: string): string {
  const withoutConstraint = tokenRaw.split(":")[0] ?? tokenRaw;
  const withoutOptional = withoutConstraint.endsWith("?")
    ? withoutConstraint.slice(0, Math.max(0, withoutConstraint.length - 1))
    : withoutConstraint;
  return withoutOptional.replace(/^\*+/, "");
}
