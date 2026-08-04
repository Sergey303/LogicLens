import type {
  HttpCallResult,
  HttpClient,
  HttpRequestDescriptor,
  HttpResponseDataByMode,
  HttpResponseMode,
} from "./httpClient";

export interface BrowserHttpClientOptions {
  apiBaseUrl?: string;
  credentials?: RequestCredentials;
  headers?: Record<string, string>;
  onUnauthorized?: (response: Response) => void;
  onForbidden?: (response: Response) => void;
}

export interface BrowserHttpErrorResponse {
  readonly data: unknown;
  readonly headers: Headers;
  readonly status: number;
}

export class BrowserHttpError extends Error {
  readonly data: unknown;
  readonly headers: Headers;
  readonly response: BrowserHttpErrorResponse;
  readonly status: number;

  constructor(response: Response, data: unknown) {
    super("HTTP " + response.status + " " + response.statusText);
    this.name = "BrowserHttpError";
    this.data = data;
    this.headers = response.headers;
    this.response = {
      data,
      headers: response.headers,
      status: response.status,
    };
    this.status = response.status;
  }
}

export function createBrowserHttpClient(options: BrowserHttpClientOptions = {}): HttpClient {
  return {
    async call<TJson, TResponseMode extends HttpResponseMode>(
      request: HttpRequestDescriptor<TResponseMode>,
    ): Promise<HttpCallResult<TJson, TResponseMode>> {
      const headers = new Headers(options.headers);
      for (const [key, value] of Object.entries(request.headers ?? {})) {
        headers.set(key, value);
      }

      const response = await fetch(resolveApiUrl(request.url, options.apiBaseUrl), {
        body: request.body ?? undefined,
        credentials: options.credentials ?? "include",
        headers,
        method: request.method,
        signal: request.signal,
      });

      if (response.status === 401) options.onUnauthorized?.(response);
      if (response.status === 403) options.onForbidden?.(response);
      if (!response.ok) {
        const errorData = await readErrorResponseData(response.clone());
        throw new BrowserHttpError(response, errorData);
      }

      return {
        data: await readResponse<TJson, TResponseMode>(response, request.responseMode),
        headers: response.headers,
        responseMode: request.responseMode,
        status: response.status,
      };
    },
  };
}

function resolveApiUrl(url: string, apiBaseUrl?: string): string {
  try {
    return new URL(url).toString();
  }
  catch {
    const normalizedUrl = url.startsWith("/") ? url : "/" + url;
    if (!apiBaseUrl || apiBaseUrl.trim().length === 0) return normalizedUrl;
    return new URL(normalizedUrl, withTrailingSlash(apiBaseUrl)).toString();
  }
}

function withTrailingSlash(value: string): string {
  const trimmed = value.trim();
  return trimmed.endsWith("/") ? trimmed : trimmed + "/";
}

async function readErrorResponseData(response: Response): Promise<unknown> {
  try {
    const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
    if (contentType.includes("json")) {
      return await response.json();
    }

    const text = await response.text();
    return text.length > 0 ? text : null;
  }
  catch {
    return null;
  }
}

async function readResponse<TJson, TResponseMode extends HttpResponseMode>(
  response: Response,
  mode: TResponseMode,
): Promise<HttpResponseDataByMode<TJson>[TResponseMode]> {
  if (mode === "none") return null as HttpResponseDataByMode<TJson>[TResponseMode];
  if (mode === "binary") return await response.blob() as HttpResponseDataByMode<TJson>[TResponseMode];
  if (mode === "stream") return readResponseStream(response) as HttpResponseDataByMode<TJson>[TResponseMode];
  if (mode === "redirect") {
    return {
      finalUrl: response.url,
      locationHeader: response.headers.get("location"),
      redirected: response.redirected,
    } as HttpResponseDataByMode<TJson>[TResponseMode];
  }
  if (response.status === 204) return null as HttpResponseDataByMode<TJson>[TResponseMode];
  return await response.json() as HttpResponseDataByMode<TJson>[TResponseMode];
}

function readResponseStream(response: Response): ReadableStream<Uint8Array> {
  if (!response.body) {
    throw new Error("[browserHttpClient] Response stream body is not available.");
  }

  return response.body;
}
