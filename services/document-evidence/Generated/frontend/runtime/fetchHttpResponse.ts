
import type {
  HttpProgressCallback,
  HttpResponseDataByMode,
  HttpResponseMode,
} from "./httpClient";
import { readResponseBytesWithProgress } from "./fetchHttpProgress";

export async function readJsonBody<TJson>(response: Response): Promise<TJson | null> {
  if (response.status === 204 || response.status === 205) {
    return null;
  }

  const text = await response.text();
  return text.trim() ? JSON.parse(text) as TJson : null;
}

export async function readResponseDataWithoutProgress<TJson, TResponseMode extends HttpResponseMode>(
  response: Response,
  responseMode: TResponseMode,
): Promise<HttpResponseDataByMode<TJson>[TResponseMode]> {
  switch (responseMode) {
    case "none":
      return null as HttpResponseDataByMode<TJson>[TResponseMode];
    case "json":
      return await readJsonBody<TJson>(response) as HttpResponseDataByMode<TJson>[TResponseMode];
    case "redirect":
      return redirectPayload(response) as HttpResponseDataByMode<TJson>[TResponseMode];
    case "binary":
      return await response.blob() as HttpResponseDataByMode<TJson>[TResponseMode];
    case "stream":
      return readResponseStream(response) as HttpResponseDataByMode<TJson>[TResponseMode];
    default:
      throw new Error(`[fetchHttpClient] Unsupported response mode '${String(responseMode)}'.`);
  }
}

export async function readResponseDataWithProgress<TJson, TResponseMode extends HttpResponseMode>(
  response: Response,
  responseMode: TResponseMode,
  onProgress: HttpProgressCallback,
): Promise<HttpResponseDataByMode<TJson>[TResponseMode]> {
  switch (responseMode) {
    case "none":
      return null as HttpResponseDataByMode<TJson>[TResponseMode];
    case "json": {
      const text = await readResponseTextWithProgress(response, onProgress);
      if (response.status === 204 || response.status === 205 || !text.trim()) {
        return null as HttpResponseDataByMode<TJson>[TResponseMode];
      }
      return JSON.parse(text) as HttpResponseDataByMode<TJson>[TResponseMode];
    }
    case "redirect":
      return redirectPayload(response) as HttpResponseDataByMode<TJson>[TResponseMode];
    case "binary": {
      const bytes = await readResponseBytesWithProgress(response, onProgress);
      const contentType = response.headers.get("content-type") ?? undefined;
      return new Blob([bytes], contentType ? { type: contentType } : undefined) as HttpResponseDataByMode<TJson>[TResponseMode];
    }
    case "stream":
      throw new Error("[fetchHttpClient] Stream response mode cannot be combined with progress buffering.");
    default:
      throw new Error(`[fetchHttpClient] Unsupported response mode '${String(responseMode)}'.`);
  }
}

export async function readErrorBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return await response.clone().json();
    } catch {
      // Fall through to text.
    }
  }

  try {
    return await response.text();
  } catch {
    return null;
  }
}

async function readResponseTextWithProgress(response: Response, onProgress: HttpProgressCallback): Promise<string> {
  return new TextDecoder().decode(await readResponseBytesWithProgress(response, onProgress));
}

function redirectPayload(response: Response): { redirected: boolean; finalUrl: string | null; locationHeader: string | null } {
  return {
    redirected: response.redirected,
    finalUrl: response.url || null,
    locationHeader: response.headers.get("location"),
  };
}

function readResponseStream(response: Response): ReadableStream<Uint8Array> {
  if (!response.body) {
    throw new Error("[fetchHttpClient] Response stream body is not available.");
  }

  return response.body;
}
