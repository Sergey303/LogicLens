
import type {
  HttpCallResult,
  HttpRequestDescriptor,
  HttpResponseMode,
} from "./httpClient";
import { readErrorBody } from "./fetchHttpResponse";
import { headersToRecord } from "./fetchHttpRequest";
import { readResponseDataWithProgress, readResponseDataWithoutProgress } from "./fetchHttpResponse";

const DEFAULT_FETCH_TIMEOUT_MS = 15000;

interface FetchRequestSignal {
  readonly signal?: AbortSignal;
  readonly cleanup: () => void;
}

export interface FetchCallOptions<TResponseMode extends HttpResponseMode> {
  request: HttpRequestDescriptor<TResponseMode>;
  url: string;
  headers: Headers;
  credentials: RequestCredentials;
  fetchImpl: typeof fetch;
}

export async function callWithFetch<TJson, TResponseMode extends HttpResponseMode>(
  options: FetchCallOptions<TResponseMode>,
): Promise<HttpCallResult<TJson, TResponseMode>> {
  const { request, url, headers, credentials, fetchImpl } = options;
  const requestSignal = createRequestSignal(request.signal, request.responseMode);

  try {
    const response = await fetchImpl(url, {
      method: request.method,
      headers,
      body: request.body ?? undefined,
      credentials,
      signal: requestSignal.signal,
      redirect: request.responseMode === "redirect" ? "manual" : "follow",
    });

    if (response.status >= 400) {
      throw {
        response: {
          status: response.status,
          data: await readErrorBody(response),
          headers: headersToRecord(response.headers),
        },
        status: response.status,
      };
    }

    const data = request.onProgress
      ? await readResponseDataWithProgress<TJson, TResponseMode>(response, request.responseMode, request.onProgress)
      : await readResponseDataWithoutProgress<TJson, TResponseMode>(response, request.responseMode);

    return {
      responseMode: request.responseMode,
      data,
      status: response.status,
      headers: response.headers,
    };
  } finally {
    requestSignal.cleanup();
  }
}

function createRequestSignal(
  requestSignal: AbortSignal | undefined,
  responseMode: HttpResponseMode,
): FetchRequestSignal {
  if (responseMode === "stream") {
    return {
      signal: requestSignal,
      cleanup: () => undefined,
    };
  }

  const timeoutController = new AbortController();
  const timeoutId = globalThis.setTimeout(
    () => timeoutController.abort(),
    DEFAULT_FETCH_TIMEOUT_MS,
  );

  if (!requestSignal) {
    return {
      signal: timeoutController.signal,
      cleanup: () => globalThis.clearTimeout(timeoutId),
    };
  }

  if (requestSignal.aborted) {
    globalThis.clearTimeout(timeoutId);
    return {
      signal: requestSignal,
      cleanup: () => undefined,
    };
  }

  const combinedController = new AbortController();
  const abortCombined = () => combinedController.abort();
  requestSignal.addEventListener("abort", abortCombined, { once: true });
  timeoutController.signal.addEventListener("abort", abortCombined, { once: true });

  return {
    signal: combinedController.signal,
    cleanup: () => {
      globalThis.clearTimeout(timeoutId);
      requestSignal.removeEventListener("abort", abortCombined);
      timeoutController.signal.removeEventListener("abort", abortCombined);
    },
  };
}
