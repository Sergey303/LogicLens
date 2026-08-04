import { mapUnknownError } from "./errorRuntime";
import { buildRequestBody, resolveBodyKind } from "./transportBody";
import { TransportRuntimeError } from "./transportErrors";
import { buildHeaders } from "./transportHeaders";
import { resolveTransportInputs } from "./transportInputs";
import { executeTransportResponse, resolveResponseKind } from "./transportResponse";
import type {
  EndpointTransportBindingMetadata,
  TransportCallOptions,
  TransportHttpRequest,
} from "./transportTypes";
import { buildUrl } from "./transportUrl";

export function defineEndpointTransport<TRequest, TResponse>(
  metadata: EndpointTransportBindingMetadata,
): (input: TRequest, options?: TransportCallOptions) => Promise<TResponse> {
  return async (input: TRequest, options?: TransportCallOptions): Promise<TResponse> => {
    try {
      const resolvedInputs = resolveTransportInputs(metadata, input);
      const bodyKind = resolveBodyKind(metadata);
      const responseKind = resolveResponseKind(metadata);
      const url = buildUrl(metadata, resolvedInputs);
      const body = buildRequestBody(metadata, input, resolvedInputs, bodyKind);
      const headers = buildHeaders(metadata, resolvedInputs, options?.headers, bodyKind, body);
      const request: TransportHttpRequest = {
        method: metadata.httpMethod,
        url,
        headers: Object.keys(headers).length > 0 ? headers : undefined,
        body,
        signal: options?.signal,
        onProgress: metadata.transport.supportsProgress === true ? options?.onProgress : undefined,
      };
      const observeResponse = options?.onResponse;

      return await executeTransportResponse<TResponse>(request, responseKind, observeResponse);
    } catch (error) {
      if (error instanceof TransportRuntimeError) {
        throw error;
      }

      throw mapUnknownError(error, metadata.errorRefs);
    }
  };
}
