import type { HttpRequestBody } from "./httpClient";
import { TransportRuntimeError, unsupportedBodyKindError } from "./transportErrors";
import { buildMultipartBody } from "./transportMultipart";
import type {
  EndpointTransportBindingMetadata,
  ResolvedTransportInput,
  SupportedBodyKind,
} from "./transportTypes";
import { appendWireValues, asInputRecord } from "./transportWireValues";

export function resolveBodyKind(metadata: EndpointTransportBindingMetadata): SupportedBodyKind {
  switch (metadata.transport.bodyKind) {
    case "none":
    case "json":
    case "multipart":
    case "form-url-encoded":
      return metadata.transport.bodyKind;
    default:
      throw unsupportedBodyKindError(metadata.transport.bodyKind, metadata);
  }
}

export function buildRequestBody<TRequest>(
  metadata: EndpointTransportBindingMetadata,
  input: TRequest,
  resolvedInputs: readonly ResolvedTransportInput[],
  bodyKind: SupportedBodyKind,
): HttpRequestBody | undefined {
  switch (bodyKind) {
    case "none":
      return undefined;
    case "json":
      return buildJsonBody(metadata, input, resolvedInputs);
    case "multipart":
      return buildMultipartBody(metadata, input);
    case "form-url-encoded":
      return buildFormUrlEncodedBody(metadata, resolvedInputs);
    default:
      throw unsupportedBodyKindError(bodyKind, metadata);
  }
}

function buildJsonBody<TRequest>(
  metadata: EndpointTransportBindingMetadata,
  input: TRequest,
  resolvedInputs: readonly ResolvedTransportInput[],
): string | undefined {
  const requestBodyMetadata = metadata.transport.requestBody;
  if (!requestBodyMetadata) {
    throw new TransportRuntimeError(
      `[transportRuntime] bodyKind 'json' requires transport.requestBody metadata for endpoint '${metadata.endpointKey}'.`,
    );
  }

  const payload = resolveJsonPayloadCandidate(input, resolvedInputs);
  if (payload === undefined && requestBodyMetadata.required) {
    throw new TransportRuntimeError(
      `[transportRuntime] Missing required JSON request body for endpoint '${metadata.endpointKey}'.`,
    );
  }

  return payload === undefined ? undefined : JSON.stringify(payload);
}

function buildFormUrlEncodedBody(
  metadata: EndpointTransportBindingMetadata,
  resolvedInputs: readonly ResolvedTransportInput[],
): URLSearchParams {
  const params = new URLSearchParams();

  for (const entry of resolvedInputs) {
    if (entry.metadata.bindingSource !== "form") {
      continue;
    }

    appendWireValues(
      entry.value,
      entry.metadata.required,
      entry.metadata.nullable,
      (value) => params.append(entry.metadata.wireName, value),
      metadata.endpointKey,
      entry.metadata.inputKey,
      "form field",
    );
  }

  return params;
}

function resolveJsonPayloadCandidate<TRequest>(
  input: TRequest,
  resolvedInputs: readonly ResolvedTransportInput[],
): unknown {
  const inputRecord = asInputRecord(input);
  if (!inputRecord) {
    return input;
  }

  if (Object.prototype.hasOwnProperty.call(inputRecord, "body")) {
    return inputRecord.body;
  }

  if (Object.prototype.hasOwnProperty.call(inputRecord, "requestBody")) {
    return inputRecord.requestBody;
  }

  if (resolvedInputs.length === 0) {
    return inputRecord;
  }

  const consumedKeys = new Set<string>(
    resolvedInputs.map((entry) => entry.matchedKey).filter((value): value is string => value !== null),
  );
  const remainingEntries = Object.entries(inputRecord).filter(([key]) => !consumedKeys.has(key));

  if (remainingEntries.length === 0) {
    return consumedKeys.size === 0 ? inputRecord : undefined;
  }

  return remainingEntries.length === 1 ? remainingEntries[0][1] : Object.fromEntries(remainingEntries);
}
