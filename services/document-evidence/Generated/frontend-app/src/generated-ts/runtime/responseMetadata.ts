export interface TransportResponseMetadata {
  readonly status: number;
  readonly headers: Headers;
  readonly warnings: readonly string[];
}

export function readTransportResponseMetadata(status: number, headers: Headers): TransportResponseMetadata {
  return {
    status,
    headers,
    warnings: readResponseWarnings(headers),
  };
}

export function readResponseWarnings(headers: Headers): readonly string[] {
  const value = headers.get("x-appforge-warnings");
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}
