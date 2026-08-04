
import type {
  HttpCallResult,
  HttpRequestDescriptor,
  HttpResponseMode,
} from "./httpClient";
import { emitProgressEvent } from "./fetchHttpProgress";
import { createAbortError } from "./fetchHttpErrors";
import { createHttpErrorFromXhr, parseXhrHeaders, readXhrResponseData, readXhrResponseText } from "./fetchHttpXhrResponse";

export interface XhrCallOptions<TResponseMode extends HttpResponseMode> {
  request: HttpRequestDescriptor<TResponseMode>;
  url: string;
  headers: Headers;
  credentials: RequestCredentials;
}

export function shouldUseXhrForProgress<TResponseMode extends HttpResponseMode>(
  request: HttpRequestDescriptor<TResponseMode>,
): boolean {
  return Boolean(
    request.onProgress
      && request.responseMode !== "redirect"
      && request.responseMode !== "stream"
      && request.body !== undefined
      && request.body !== null,
  );
}

export async function callWithXhr<TJson, TResponseMode extends HttpResponseMode>(
  options: XhrCallOptions<TResponseMode>,
): Promise<HttpCallResult<TJson, TResponseMode>> {
  const { request, url, headers, credentials } = options;

  return new Promise<HttpCallResult<TJson, TResponseMode>>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(request.method, url, true);
    xhr.withCredentials = credentials === "include";
    xhr.responseType = request.responseMode === "binary" ? "blob" : "text";
    headers.forEach((value, key) => xhr.setRequestHeader(key, value));

    const cleanupHandlers = bindAbortHandler(xhr, request, reject);
    bindProgressHandlers(xhr, request);
    xhr.onerror = () => rejectWithCleanup(cleanupHandlers, reject, new Error("[fetchHttpClient] XMLHttpRequest network error."));
    xhr.onabort = () => rejectWithCleanup(cleanupHandlers, reject, createAbortError());
    xhr.onload = () => handleXhrLoad(xhr, request, url, cleanupHandlers, resolve, reject);
    xhr.send(toXhrRequestBody(request.body));
  });
}

function bindAbortHandler<TResponseMode extends HttpResponseMode>(
  xhr: XMLHttpRequest,
  request: HttpRequestDescriptor<TResponseMode>,
  reject: (reason?: unknown) => void,
): Array<() => void> {
  if (!request.signal) {
    return [];
  }

  const onAbort = () => xhr.abort();
  if (request.signal.aborted) {
    reject(createAbortError());
    return [];
  }

  request.signal.addEventListener("abort", onAbort, { once: true });
  return [() => request.signal?.removeEventListener("abort", onAbort)];
}

function bindProgressHandlers<TResponseMode extends HttpResponseMode>(
  xhr: XMLHttpRequest,
  request: HttpRequestDescriptor<TResponseMode>,
): void {
  const onProgress = request.onProgress;
  if (!onProgress) {
    return;
  }

  xhr.onprogress = (event) => emitProgressEvent(onProgress, "download", event.loaded, event.total, event.lengthComputable);
  if (xhr.upload) {
    xhr.upload.onprogress = (event) => emitProgressEvent(onProgress, "upload", event.loaded, event.total, event.lengthComputable);
  }
}

function handleXhrLoad<TJson, TResponseMode extends HttpResponseMode>(
  xhr: XMLHttpRequest,
  request: HttpRequestDescriptor<TResponseMode>,
  url: string,
  cleanupHandlers: Array<() => void>,
  resolve: (value: HttpCallResult<TJson, TResponseMode>) => void,
  reject: (reason?: unknown) => void,
): void {
  cleanup(cleanupHandlers);
  const responseHeaders = parseXhrHeaders(xhr.getAllResponseHeaders());
  if (xhr.status >= 400) {
    reject(createHttpErrorFromXhr(xhr.status, responseHeaders, readXhrResponseText(xhr)));
    return;
  }

  try {
    resolve({
      responseMode: request.responseMode,
      data: readXhrResponseData<TJson, TResponseMode>(xhr, request.responseMode, responseHeaders, url),
      status: xhr.status,
      headers: responseHeaders,
    });
  } catch (error) {
    reject(error);
  }
}

function toXhrRequestBody(body: HttpRequestDescriptor["body"]): XMLHttpRequestBodyInit | Document | null {
  if (body === undefined || body === null) {
    return null;
  }

  if (typeof ReadableStream !== "undefined" && body instanceof ReadableStream) {
    throw new Error("[fetchHttpClient] XMLHttpRequest upload progress does not support ReadableStream request bodies.");
  }

  return body as XMLHttpRequestBodyInit | Document;
}

function rejectWithCleanup(cleanupHandlers: Array<() => void>, reject: (reason?: unknown) => void, error: unknown): void {
  cleanup(cleanupHandlers);
  reject(error);
}

function cleanup(cleanupHandlers: Array<() => void>): void {
  for (const dispose of cleanupHandlers) {
    dispose();
  }
}
