
import type { StaticOrDynamicHeaders } from "./fetchHttpClient";

export async function resolveHeaders(
  headers: StaticOrDynamicHeaders | undefined,
): Promise<Record<string, string>> {
  if (!headers) {
    return {};
  }

  return typeof headers === "function" ? await headers() : headers;
}

export function resolveUrl(baseUrl: string, requestUrl: string): string {
  if (/^https?:\/\//i.test(requestUrl)) {
    return requestUrl;
  }

  return new URL(requestUrl, ensureTrailingSlash(baseUrl)).toString();
}

function ensureTrailingSlash(value: string): string {
  return value.endsWith("/") ? value : `${value}/`;
}

export function headersToRecord(headers: Headers): Record<string, string> {
  const record: Record<string, string> = {};
  headers.forEach((value, key) => {
    record[key] = value;
  });
  return record;
}
