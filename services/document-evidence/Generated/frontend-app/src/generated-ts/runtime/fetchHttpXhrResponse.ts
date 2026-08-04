
import type { HttpResponseDataByMode, HttpResponseMode } from "./httpClient";
import { headersToRecord } from "./fetchHttpRequest";

export function createHttpErrorFromXhr(
  status: number,
  responseHeaders: Headers,
  responseText: string,
): { response: { status: number; data: unknown; headers: Record<string, string> }; status: number } {
  return {
    response: {
      status,
      data: parseXhrErrorBody(responseHeaders, responseText),
      headers: headersToRecord(responseHeaders),
    },
    status,
  };
}

export function parseXhrHeaders(rawHeaders: string): Headers {
  const headers = new Headers();
  for (const line of rawHeaders.split(/\r?\n/)) {
    const delimiterIndex = line.indexOf(":");
    if (delimiterIndex <= 0) {
      continue;
    }

    const key = line.slice(0, delimiterIndex).trim();
    const value = line.slice(delimiterIndex + 1).trim();
    if (key) {
      headers.append(key, value);
    }
  }

  return headers;
}

export function readXhrResponseData<TJson, TResponseMode extends HttpResponseMode>(
  xhr: XMLHttpRequest,
  responseMode: TResponseMode,
  headers: Headers,
  requestUrl: string,
): HttpResponseDataByMode<TJson>[TResponseMode] {
  switch (responseMode) {
    case "none":
      return null as HttpResponseDataByMode<TJson>[TResponseMode];
    case "json":
      return parseXhrJsonBody<TJson>(xhr) as HttpResponseDataByMode<TJson>[TResponseMode];
    case "redirect":
      return {
        redirected: isRedirectedByXhr(requestUrl, xhr.responseURL, xhr.status),
        finalUrl: xhr.responseURL || null,
        locationHeader: headers.get("location"),
      } as HttpResponseDataByMode<TJson>[TResponseMode];
    case "binary":
      return (xhr.response instanceof Blob ? xhr.response : new Blob([readXhrResponseText(xhr)])) as HttpResponseDataByMode<TJson>[TResponseMode];
    case "stream":
      throw new Error("[fetchHttpClient] Stream response mode is not supported by XMLHttpRequest.");
    default:
      throw new Error(`[fetchHttpClient] Unsupported response mode '${String(responseMode)}'.`);
  }
}

export function readXhrResponseText(xhr: XMLHttpRequest): string {
  try {
    return xhr.responseText ?? "";
  } catch {
    return "";
  }
}

function parseXhrJsonBody<TJson>(xhr: XMLHttpRequest): TJson | null {
  if (xhr.status === 204 || xhr.status === 205) {
    return null;
  }

  const text = readXhrResponseText(xhr);
  return text.trim() ? JSON.parse(text) as TJson : null;
}

function parseXhrErrorBody(headers: Headers, responseText: string): unknown {
  const contentType = headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return responseText;
  }

  try {
    return JSON.parse(responseText);
  } catch {
    return responseText;
  }
}

function isRedirectedByXhr(requestUrl: string, responseUrl: string, status: number): boolean {
  if (status >= 300 && status < 400) {
    return true;
  }

  return Boolean(responseUrl && responseUrl !== requestUrl);
}
