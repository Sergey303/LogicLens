import { TransportRuntimeError } from "./transportErrors";
import type { EndpointTransportBindingMetadata } from "./transportTypes";
import { asInputRecord, isBlobLike, isPrimitiveWireValue } from "./transportWireValues";

export function buildMultipartBody<TRequest>(
  metadata: EndpointTransportBindingMetadata,
  input: TRequest,
): FormData {
  const formData = new FormData();
  const inputRecord = asInputRecord(input);
  for (const part of metadata.transport.multipartParts) {
    const partValue = readMultipartPartValue(inputRecord, part.partKey, part.wireName);

    if (partValue === undefined || partValue === null) {
      if (part.required) {
        throw new TransportRuntimeError(
          `[transportRuntime] Missing required multipart part '${part.partKey}' for endpoint '${metadata.endpointKey}'.`,
        );
      }
      continue;
    }

    const coercedValue = coerceMultipartValueByContentKinds(partValue, part.contentKinds);
    appendMultipartValue(formData, part.wireName, coercedValue, metadata.endpointKey, part.partKey);
  }

  return formData;
}

function appendMultipartValue(
  formData: FormData,
  wireName: string,
  value: unknown,
  endpointKey: string,
  inputKey: string,
): void {
  if (value === undefined || value === null) {
    return;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      appendMultipartSingleValue(formData, wireName, item, endpointKey, inputKey);
    }
    return;
  }

  appendMultipartSingleValue(formData, wireName, value, endpointKey, inputKey);
}

function appendMultipartSingleValue(
  formData: FormData,
  wireName: string,
  value: unknown,
  endpointKey: string,
  inputKey: string,
): void {
  if (isBlobLike(value)) {
    formData.append(wireName, value);
    return;
  }

  if (value instanceof Date) {
    formData.append(wireName, value.toISOString());
    return;
  }

  if (isPrimitiveWireValue(value)) {
    formData.append(wireName, String(value));
    return;
  }

  if (value && typeof value === "object") {
    formData.append(wireName, JSON.stringify(value));
    return;
  }

  throw new TransportRuntimeError(
    `[transportRuntime] Unsupported multipart part value for '${inputKey}' on endpoint '${endpointKey}'.`,
  );
}

function readMultipartPartValue(
  inputRecord: Record<string, unknown> | null,
  partKey: string,
  wireName: string,
): unknown {
  if (!inputRecord) {
    return undefined;
  }

  if (Object.prototype.hasOwnProperty.call(inputRecord, partKey)) {
    return inputRecord[partKey];
  }

  if (Object.prototype.hasOwnProperty.call(inputRecord, wireName)) {
    return inputRecord[wireName];
  }

  return undefined;
}

function coerceMultipartValueByContentKinds(value: unknown, contentKinds: readonly string[]): unknown {
  if (!contentKinds || contentKinds.length === 0) {
    return value;
  }

  if (isBinaryContent(contentKinds)) {
    return coerceBinaryMultipartValue(value, contentKinds[0]);
  }

  if (isTextContent(contentKinds) && typeof value !== "string") {
    return String(value);
  }

  return value;
}

function coerceBinaryMultipartValue(value: unknown, contentType: string | undefined): unknown {
  if (isBlobLike(value)) {
    return value;
  }

  if (typeof value === "string" || (value && typeof value === "object")) {
    try {
      const blobContent = typeof value === "string" ? value : JSON.stringify(value);
      return new Blob([blobContent], { type: contentType });
    } catch {
      return value;
    }
  }

  return value;
}

function isBinaryContent(contentKinds: readonly string[]): boolean {
  return contentKinds.some(
    (kind) => kind === "application/octet-stream"
      || kind.startsWith("image/")
      || kind.startsWith("video/")
      || kind.startsWith("audio/")
      || kind.includes("binary"),
  );
}

function isTextContent(contentKinds: readonly string[]): boolean {
  return contentKinds.some(
    (kind) => kind === "text/plain" || kind.startsWith("text/") || kind.includes("text"),
  );
}
