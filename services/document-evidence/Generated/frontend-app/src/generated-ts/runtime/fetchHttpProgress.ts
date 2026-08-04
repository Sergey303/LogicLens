
import type { HttpProgressCallback } from "./httpClient";

export async function readResponseBytesWithProgress(
  response: Response,
  onProgress: HttpProgressCallback,
): Promise<Uint8Array<ArrayBuffer>> {
  const expectedTotal = parseContentLength(response.headers.get("content-length"));

  if (!response.body) {
    const fallbackBlob = await response.blob();
    emitProgressEvent(onProgress, "download", fallbackBlob.size, fallbackBlob.size, true);
    return new Uint8Array(await fallbackBlob.arrayBuffer());
  }

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    if (!value) {
      continue;
    }

    chunks.push(value);
    loaded += value.byteLength;
    emitProgressEvent(onProgress, "download", loaded, expectedTotal, expectedTotal !== null);
  }

  if (expectedTotal !== null && loaded !== expectedTotal) {
    emitProgressEvent(onProgress, "download", loaded, expectedTotal, true);
  }

  return concatChunks(chunks, loaded);
}

export function emitProgressEvent(
  onProgress: HttpProgressCallback,
  kind: "upload" | "download",
  loaded: number,
  total: number | null,
  lengthComputable: boolean,
): void {
  onProgress({
    kind,
    loaded,
    total: lengthComputable ? total : null,
    lengthComputable,
  });
}

function concatChunks(chunks: Uint8Array[], totalBytes: number): Uint8Array<ArrayBuffer> {
  const output = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return output;
}

function parseContentLength(contentLengthHeader: string | null): number | null {
  if (!contentLengthHeader) {
    return null;
  }

  const parsed = Number.parseInt(contentLengthHeader, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}
