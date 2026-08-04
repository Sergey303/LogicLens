import type { HttpCallResult, HttpResponseMode } from "./httpClient";
import { getHttpClient } from "./httpClient";
import { readTransportResponseMetadata } from "./responseMetadata";
import { readNdjsonStream } from "./streamRuntime";
import { TransportRuntimeError, unsupportedResponseKindError } from "./transportErrors";
import { extractFileNameFromContentDisposition } from "./transportFileName";
import type {
  BinaryTransportPayload,
  EndpointTransportBindingMetadata,
  SupportedResponseKind,
  TransportHttpRequest,
  TransportResponseObserver,
} from "./transportTypes";

export function resolveResponseKind(
  metadata: EndpointTransportBindingMetadata,
): SupportedResponseKind {
  const topLevelKind = metadata.transport.responseKind;
  const nestedKind = metadata.transport.response?.responseKind;

  if (nestedKind && topLevelKind && nestedKind !== topLevelKind) {
    throw new TransportRuntimeError(
      `[transportRuntime] Response kind mismatch for endpoint '${metadata.endpointKey}': transport.responseKind='${topLevelKind}', transport.response.responseKind='${nestedKind}'.`,
    );
  }

  const effectiveKind = topLevelKind || nestedKind || "";

  switch (effectiveKind) {
    case "none":
    case "json":
    case "redirect":
    case "binary":
    case "stream":
      return effectiveKind;
    default:
      throw unsupportedResponseKindError(effectiveKind, metadata);
  }
}

export async function executeTransportResponse<TResponse>(
  request: TransportHttpRequest,
  responseKind: SupportedResponseKind,
  onResponse?: TransportResponseObserver,
): Promise<TResponse> {
  const httpClient = getHttpClient();

  switch (responseKind) {
    case "none": {
      const result = await httpClient.call<never, "none">({ ...request, responseMode: "none" });
      notifyResponse(result, onResponse);
      return undefined as TResponse;
    }
    case "json": {
      const result = await httpClient.call<TResponse, "json">({ ...request, responseMode: "json" });
      notifyResponse(result, onResponse);
      return result.data;
    }
    case "redirect": {
      const result = await httpClient.call<never, "redirect">({ ...request, responseMode: "redirect" });
      notifyResponse(result, onResponse);
      return (result.data.locationHeader ?? result.data.finalUrl) as unknown as TResponse;
    }
    case "binary": {
      const result = await httpClient.call<never, "binary">({ ...request, responseMode: "binary" });
      notifyResponse(result, onResponse);
      const contentDisposition = result.headers.get("content-disposition");
      const binaryPayload: BinaryTransportPayload = {
        blob: result.data,
        status: result.status,
        headers: result.headers,
        contentType: result.headers.get("content-type"),
        contentDisposition,
        fileName: extractFileNameFromContentDisposition(contentDisposition),
      };
      return binaryPayload as unknown as TResponse;
    }
    case "stream": {
      const result = await httpClient.call<never, "stream">({ ...request, responseMode: "stream" });
      notifyResponse(result, onResponse);
      return readNdjsonStream<unknown>(result.data) as unknown as TResponse;
    }
    default: {
      return assertNeverResponseKind(responseKind);
    }
  }
}

function notifyResponse<TJson, TResponseMode extends HttpResponseMode>(
  result: HttpCallResult<TJson, TResponseMode>,
  onResponse: TransportResponseObserver | undefined,
): void {
  onResponse?.(readTransportResponseMetadata(result.status, result.headers));
}

function assertNeverResponseKind(value: never): never {
  throw new TransportRuntimeError(`[transportRuntime] Unsupported responseKind '${value}'.`);
}
