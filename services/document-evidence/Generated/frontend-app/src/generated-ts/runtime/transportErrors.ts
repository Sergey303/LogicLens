import type { EndpointTransportBindingMetadata } from "./transportTypes";

export class TransportRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TransportRuntimeError";
  }
}

export function unsupportedBindingSourceError(
  bindingSource: string,
  metadata: EndpointTransportBindingMetadata,
): TransportRuntimeError {
  return new TransportRuntimeError(
    `[transportRuntime] Unsupported bindingSource '${bindingSource}' for endpoint '${metadata.endpointKey}'.`,
  );
}

export function unsupportedBodyKindError(
  bodyKind: string,
  metadata: EndpointTransportBindingMetadata,
): TransportRuntimeError {
  return new TransportRuntimeError(
    `[transportRuntime] Unsupported bodyKind '${bodyKind}' for endpoint '${metadata.endpointKey}'.`,
  );
}

export function unsupportedResponseKindError(
  responseKind: string,
  metadata: EndpointTransportBindingMetadata,
): TransportRuntimeError {
  return new TransportRuntimeError(
    `[transportRuntime] Unsupported responseKind '${responseKind}' for endpoint '${metadata.endpointKey}'.`,
  );
}
