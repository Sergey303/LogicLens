export type QueryKeyPart =
  | string
  | number
  | boolean
  | null
  | undefined
  | QueryKeyObject
  | QueryKeyPart[];

export interface QueryKeyObject {
  readonly [key: string]: QueryKeyPart;
}

export type QueryKey = readonly QueryKeyPart[];

export function buildEndpointQueryKey(
  endpointKey: string,
  input: unknown,
): QueryKey {
  return [endpointKey, normalizeKeyPart(input)] as const;
}

class QueryKeyNormalizationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "QueryKeyNormalizationError";
  }
}

function normalizeKeyPart(value: unknown): QueryKeyPart {
  // Handle null and undefined
  if (value == null) {
    return value;
  }

  // Handle primitives
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  // Handle Date objects
  if (value instanceof Date) {
    return value.toISOString();
  }

  // Handle arrays
  if (Array.isArray(value)) {
    return value.map(normalizeKeyPart);
  }

  // Handle plain objects
  if (typeof value === "object") {
    // Check if it's a plain object (not a class instance, Blob, etc.)
    const proto = Object.getPrototypeOf(value);
    if (proto !== null && proto !== Object.prototype) {
      // Reject class instances and other non-plain objects
      throw new QueryKeyNormalizationError(
        `Unsupported object type in query key: ${value.constructor?.name || "unknown"}. ` +
        "Only plain objects, arrays, primitives, null, undefined, and Date values are allowed."
      );
    }

    const normalized: Record<string, QueryKeyPart> = {};
    // Sort keys for stable ordering
    for (const [key, entry] of Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b))) {
      normalized[key] = normalizeKeyPart(entry);
    }
    return normalized;
  }

  // Reject all other types (functions, symbols, bigint, etc.)
  throw new QueryKeyNormalizationError(
    `Unsupported value type in query key: ${typeof value}. ` +
    "Only primitives, arrays, plain objects, null, undefined, and Date values are allowed."
  );
}

