// Production note: frontend must call configureHttpClient before executing generated bindings.
export type HttpResponseMode = "none" | "json" | "redirect" | "binary" | "stream";

export interface RedirectHttpPayload {
  redirected: boolean;
  finalUrl: string | null;
  locationHeader: string | null;
}

export interface HttpResponseDataByMode<TJson> {
  none: null;
  json: TJson;
  redirect: RedirectHttpPayload;
  binary: Blob;
  stream: ReadableStream<Uint8Array>;
}

export type HttpProgressKind = "upload" | "download";

export interface HttpProgressEvent {
  kind: HttpProgressKind;
  loaded: number;
  total: number | null;
  lengthComputable: boolean;
}

export type HttpProgressCallback = (event: HttpProgressEvent) => void;

export type HttpRequestBody = BodyInit | URLSearchParams | FormData | null;

export interface HttpRequestDescriptor<TResponseMode extends HttpResponseMode = HttpResponseMode> {
  method: string;
  url: string;
  headers?: Record<string, string>;
  body?: HttpRequestBody;
  signal?: AbortSignal;
  onProgress?: HttpProgressCallback;
  responseMode: TResponseMode;
}

export interface HttpCallResult<TJson, TResponseMode extends HttpResponseMode> {
  responseMode: TResponseMode;
  data: HttpResponseDataByMode<TJson>[TResponseMode];
  status: number;
  headers: Headers;
}

export interface HttpClient {
  call<TJson, TResponseMode extends HttpResponseMode>(
    request: HttpRequestDescriptor<TResponseMode>,
  ): Promise<HttpCallResult<TJson, TResponseMode>>;
}

export class MissingHttpClientError extends Error {
  constructor() {
    super("No HttpClient has been configured for the generated runtime.");
  }
}

let currentHttpClient: HttpClient | null = null;

export function configureHttpClient(httpClient: HttpClient): void {
  currentHttpClient = httpClient;
}

export function getHttpClient(): HttpClient {
  if (!currentHttpClient) {
    throw new MissingHttpClientError();
  }

  return currentHttpClient;
}
