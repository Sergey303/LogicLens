import type { HttpProgressCallback, HttpRequestBody } from "./httpClient";
import type { TransportResponseMetadata } from "./responseMetadata";

export type TransportResponseObserver = (metadata: TransportResponseMetadata) => void;

export interface TransportCallOptions {
  signal?: AbortSignal;
  headers?: Record<string, string>;
  onProgress?: HttpProgressCallback;
  onResponse?: TransportResponseObserver;
}

export interface EndpointTransportInput {
  inputKey: string;
  bindingSource: string;
  name: string;
  wireName: string;
  typeRef: string;
  nullable: boolean;
  required: boolean;
}

export interface RequestBodyMetadata {
  typeRef: string;
  required: boolean;
}

export interface MultipartPart {
  partKey: string;
  wireName: string;
  typeRef: string;
  required: boolean;
  contentKinds: readonly string[];
  acceptedMimeTypes: readonly string[];
  maxFileSizeBytes: number | null;
  fileNameSource: string | null;
}

export interface EndpointResponseMetadata {
  responseKind: string;
  responseContentType: string | null;
  typeRef: string | null;
  contentDisposition: string | null;
  fileNameSource: string | null;
}

export interface EndpointAuthorizationMetadata {
  anonymousAllowed: boolean;
  requiresAuthentication: boolean;
  policyNames: readonly string[];
}

export interface EndpointTransportMetadata {
  bodyKind: string;
  requestContentType: string | null;
  responseKind: string;
  responseContentType: string | null;
  transportKind: string | null;
  operationMode: string | null;
  cancellable: boolean | null;
  supportsProgress: boolean | null;
  progressEventKeys: readonly string[];
  completionEventKeys: readonly string[];
  resultDelivery: string | null;
  acceptedMimeTypes: readonly string[];
  maxFileSizeBytes: number | null;
  fileNameSource: string | null;
  inputs: readonly EndpointTransportInput[];
  requestBody: RequestBodyMetadata | null;
  multipartParts: readonly MultipartPart[];
  response: EndpointResponseMetadata | null;
}

export interface FrontendActionMetadata {
  actionKind: string;
  featureKey: string | null;
  policyKey: string | null;
  capabilityKey: string | null;
  environmentScopes: readonly string[];
  disabledReasonKey: string | null;
}

export interface EndpointTransportBindingMetadata {
  endpointKey: string;
  domainKey: string;
  kind: string;
  controllerName: string;
  methodName: string;
  httpMethod: string;
  routeTemplate: string;
  authorization: EndpointAuthorizationMetadata;
  transport: EndpointTransportMetadata;
  featureKeys: readonly string[];
  policyKeys: readonly string[];
  capabilityKeys: readonly string[];
  providerKeys: readonly string[];
  environmentScopes: readonly string[];
  disabledReasonKey: string | null;
  errorRefs: readonly string[];
  invalidatesEndpointKeys: readonly string[];
  realtimeLinks: readonly string[];
  invalidatedByRealtimeEventKeys: readonly string[];
  frontendAction: FrontendActionMetadata | null;
  requestTypeRef: string | null;
  responseTypeRef: string | null;
}

export interface BinaryTransportPayload {
  blob: Blob;
  status: number;
  headers: Headers;
  contentType: string | null;
  contentDisposition: string | null;
  fileName: string | null;
}

export type SupportedBindingSource = "route" | "query" | "header" | "form";
export type SupportedBodyKind = "none" | "json" | "multipart" | "form-url-encoded";
export type SupportedResponseKind = "none" | "json" | "redirect" | "binary" | "stream";

export interface ResolvedTransportInput {
  metadata: EndpointTransportInput;
  value: unknown;
  matchedKey: string | null;
}

export interface TransportHttpRequest {
  method: string;
  url: string;
  headers?: Record<string, string>;
  body?: HttpRequestBody;
  signal?: AbortSignal;
  onProgress?: HttpProgressCallback;
}
