import { TransportRuntimeError } from "./transportErrors";

export function appendWireValues(
  value: unknown,
  required: boolean,
  nullable: boolean,
  append: (value: string) => void,
  endpointKey: string,
  inputKey: string,
  context: string,
): void {
  if (value === undefined || (value === null && !nullable)) {
    if (required) {
      throw new TransportRuntimeError(
        `[transportRuntime] Missing required ${context} '${inputKey}' for endpoint '${endpointKey}'.`,
      );
    }
    return;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      append(toWireString(item, context, endpointKey, inputKey));
    }
    return;
  }

  append(toWireString(value, context, endpointKey, inputKey));
}

export function toHeaderString(value: unknown, endpointKey: string, inputKey: string): string {
  if (Array.isArray(value)) {
    return value.map((item) => toWireString(item, "header input", endpointKey, inputKey)).join(",");
  }

  return toWireString(value, "header input", endpointKey, inputKey);
}

export function toWireString(
  value: unknown,
  context: string,
  endpointKey: string,
  inputKey: string,
): string {
  if (value === null) {
    return "null";
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (isPrimitiveWireValue(value)) {
    return String(value);
  }

  throw new TransportRuntimeError(
    `[transportRuntime] ${context} '${inputKey}' for endpoint '${endpointKey}' must be a primitive or Date value.`,
  );
}

export function asInputRecord<TRequest>(input: TRequest): Record<string, unknown> | null {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return null;
  }

  if (input instanceof Date || input instanceof FormData || input instanceof URLSearchParams || isBlobLike(input)) {
    return null;
  }

  return input as Record<string, unknown>;
}

export function isPrimitiveWireValue(value: unknown): value is string | number | boolean | bigint {
  return (
    typeof value === "string"
    || typeof value === "number"
    || typeof value === "boolean"
    || typeof value === "bigint"
  );
}

export function isBlobLike(value: unknown): value is Blob {
  return typeof Blob !== "undefined" && value instanceof Blob;
}
