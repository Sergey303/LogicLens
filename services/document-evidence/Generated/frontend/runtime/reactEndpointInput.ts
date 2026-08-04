
import type { GeneratedEndpointInput } from "./reactQueryTypes";

export function normalizeEndpointInput<TInput>(input: GeneratedEndpointInput<TInput>): unknown {
  if (!isRecord(input)) {
    return input;
  }

  const hasArgs = isRecord(input.args);
  const hasRequest = Object.prototype.hasOwnProperty.call(input, "request");
  if (!hasArgs && !hasRequest) {
    return input;
  }

  if (hasArgs) {
    const normalized: Record<string, unknown> = { ...input.args };
    if (hasRequest) {
      normalized.body = input.request;
    }
    return normalized;
  }

  const { request, ...rest } = input;
  if (Object.keys(rest).length === 0) {
    return request;
  }

  return {
    ...rest,
    body: request,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
