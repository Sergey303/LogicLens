import type { HttpRequestBody } from "./httpClient";
import type {
  EndpointTransportBindingMetadata,
  ResolvedTransportInput,
  SupportedBodyKind,
} from "./transportTypes";
import { toHeaderString } from "./transportWireValues";

export function buildHeaders(
  metadata: EndpointTransportBindingMetadata,
  resolvedInputs: readonly ResolvedTransportInput[],
  optionHeaders: Record<string, string> | undefined,
  bodyKind: SupportedBodyKind,
  body: HttpRequestBody | undefined,
): Record<string, string> {
  const headers: Record<string, string> = { ...(optionHeaders ?? {}) };

  for (const entry of resolvedInputs) {
    if (entry.metadata.bindingSource !== "header") {
      continue;
    }

    if (entry.value === undefined || entry.value === null) {
      continue;
    }

    headers[entry.metadata.wireName] = toHeaderString(
      entry.value,
      metadata.endpointKey,
      entry.metadata.inputKey,
    );
  }

  if (body === undefined || body === null) {
    return headers;
  }

  const requestContentType = metadata.transport.requestContentType;
  if (bodyKind === "json") {
    ensureHeader(headers, "Content-Type", requestContentType ?? "application/json");
  } else if (bodyKind === "form-url-encoded") {
    ensureHeader(headers, "Content-Type", requestContentType ?? "application/x-www-form-urlencoded");
  }

  return headers;
}

function ensureHeader(headers: Record<string, string>, key: string, value: string): void {
  const existing = Object.keys(headers).some(
    (currentKey) => currentKey.toLowerCase() === key.toLowerCase(),
  );
  if (!existing) {
    headers[key] = value;
  }
}
