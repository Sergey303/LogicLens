import { errorFamilyByCode } from "../shared/contracts/errors/errorFamilyByCode.generated";
import type { FrontendErrorSeverity } from "./errorTypes";

export const standardApiErrorCodes = [
  "auth.authentication_required",
  "conflict",
  "forbidden",
  "network_unavailable",
  "not_found",
  "rate_limited",
  "validation_failed",
] as const;

const standardApiErrorCodeSet = new Set<string>(standardApiErrorCodes);

export function isAcceptedErrorCode(errorCode: string | null, errorRefs: readonly string[]): errorCode is string {
  return Boolean(errorCode && (errorRefs.includes(errorCode) || standardApiErrorCodeSet.has(errorCode)));
}

export function resolveErrorFamilyKey(errorCode: string): string | null {
  return errorFamilyByCode[errorCode] ?? null;
}

export function inferDomainKey(_errorCode: string, _errorFamilyKey: string | null): string | null {
  return null;
}

export function normalizeSeverity(value: unknown): FrontendErrorSeverity {
  switch (value) {
    case "warning":
    case "info":
    case "error":
      return value;
    default:
      return "error";
  }
}
