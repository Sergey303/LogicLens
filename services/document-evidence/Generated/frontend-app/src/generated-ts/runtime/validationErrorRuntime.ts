export function readFieldErrors(error: unknown): Record<string, string> {
  const data = readErrorData(error);
  const errors = asRecord(asRecord(data)?.errors);
  if (!errors) {
    return {};
  }

  const result: Record<string, string> = {};
  for (const [field, value] of Object.entries(errors)) {
    const message = readFirstErrorMessage(value);
    const normalizedField = normalizeFieldKey(field);
    if (normalizedField && message) {
      result[normalizedField] = message;
    }
  }

  return result;
}

function readErrorData(error: unknown): unknown {
  const root = asRecord(error);
  const details = asRecord(root?.details);
  const detailsErrors = asRecord(details?.errors);
  if (detailsErrors) {
    return details;
  }

  const response = asRecord(root?.response);
  return response?.data ?? root?.data ?? details ?? null;
}

function readFirstErrorMessage(value: unknown): string | null {
  if (Array.isArray(value)) {
    const first = value.find((item) => typeof item === "string" && item.trim().length > 0);
    return typeof first === "string" ? first : null;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }

  return null;
}

function normalizeFieldKey(value: string): string {
  const normalized = value
    .replace(/\[[^\]]*\]/g, "")
    .split(".")
    .filter((part) => part.length > 0)
    .pop() ?? value;

  if (!normalized) {
    return "";
  }

  return normalized.slice(0, 1).toLowerCase() + normalized.slice(1);
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
}
