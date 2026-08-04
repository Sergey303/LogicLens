
import type {
  HttpCallResult,
  HttpClient,
  HttpRequestDescriptor,
  HttpResponseMode,
} from "./httpClient";
import { callWithFetch } from "./fetchHttpFetchCall";
import { callWithXhr, shouldUseXhrForProgress } from "./fetchHttpXhrCall";
import { resolveHeaders, resolveUrl } from "./fetchHttpRequest";

export type StaticOrDynamicHeaders =
  | Record<string, string>
  | (() => Record<string, string> | Promise<Record<string, string>>);

export interface FetchHttpClientOptions {
  readonly baseUrl: string;
  readonly credentials?: RequestCredentials;
  readonly headers?: StaticOrDynamicHeaders;
  readonly fetchImpl?: typeof fetch;
}

export function createFetchHttpClient(options: FetchHttpClientOptions): HttpClient {
  return new FetchHttpClient(options);
}

class FetchHttpClient implements HttpClient {
  private readonly baseUrl: string;
  private readonly credentials: RequestCredentials;
  private readonly headers?: StaticOrDynamicHeaders;
  private readonly fetchImpl: typeof fetch;

  constructor(options: FetchHttpClientOptions) {
    this.baseUrl = options.baseUrl;
    this.credentials = options.credentials ?? "include";
    this.headers = options.headers;
    const fetchImpl = options.fetchImpl ?? globalThis.fetch;
    if (!fetchImpl) {
      throw new Error("[fetchHttpClient] global fetch is not available. Pass fetchImpl explicitly.");
    }
    this.fetchImpl = fetchImpl.bind(globalThis);
  }

  async call<TJson, TResponseMode extends HttpResponseMode>(
    request: HttpRequestDescriptor<TResponseMode>,
  ): Promise<HttpCallResult<TJson, TResponseMode>> {
    const headers = new Headers(await resolveHeaders(this.headers));

    for (const [key, value] of Object.entries(request.headers ?? {})) {
      headers.set(key, value);
    }

    const resolvedUrl = resolveUrl(this.baseUrl, request.url);
    if (shouldUseXhrForProgress(request)) {
      return callWithXhr<TJson, TResponseMode>({
        request,
        url: resolvedUrl,
        headers,
        credentials: this.credentials,
      });
    }

    return callWithFetch<TJson, TResponseMode>({
      request,
      url: resolvedUrl,
      headers,
      credentials: this.credentials,
      fetchImpl: this.fetchImpl,
    });
  }
}
