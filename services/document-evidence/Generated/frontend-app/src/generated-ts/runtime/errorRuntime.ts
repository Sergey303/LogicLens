
import { inferDomainKey, normalizeSeverity, resolveErrorFamilyKey } from "./errorCodeRuntime";
import { parseCanonicalError } from "./errorParsers";
import type { ErrorCatalogRef, FrontendDomainError, RealtimeErrorEnvelope, RestErrorEnvelope } from "./errorTypes";
import { firstString, getRecord, serializeUnknownError, toNumber } from "./errorValueUtils";


export function mapUnknownError(error: unknown, errorRefs: readonly string[]): FrontendDomainError {
  if (isFrontendDomainError(error)) {
    return normalizeFrontendDomainError(error);
  }

  const parsed = parseCanonicalError(error, errorRefs);
  if (parsed) {
    return {
      domainKey: parsed.domainKey,
      errorCode: parsed.errorCode,
      i18nKey: null,
      severity: parsed.severity ?? "error",
      userDisplayable: parsed.userDisplayable ?? true,
      details: parsed.details,
      httpStatus: parsed.httpStatus,
      retryable: parsed.retryable,
    };
  }

  const httpError = mapHttpErrorFallback(error, errorRefs);
  return httpError ?? {
    domainKey: null,
    errorCode: "unknown_error",
    i18nKey: null,
    severity: "error",
    userDisplayable: true,
    details: {
      errorRefs,
      originalError: serializeUnknownError(error),
    },
  };
}

export function isFrontendDomainError(value: unknown): value is FrontendDomainError {
  return typeof value === "object" && value !== null && "errorCode" in value;
}

function normalizeFrontendDomainError(error: FrontendDomainError): FrontendDomainError {
  const familyKey = resolveErrorFamilyKey(error.errorCode);
  return {
    ...error,
    domainKey: error.domainKey ?? inferDomainKey(error.errorCode, familyKey),
    severity: normalizeSeverity(error.severity),
  };
}

function mapHttpErrorFallback(error: unknown, errorRefs: readonly string[]): FrontendDomainError | null {
  const errorRecord = getRecord(error);
  const responseRecord = getRecord(errorRecord?.response);
  const httpStatus = toNumber(responseRecord?.status) ?? toNumber(errorRecord?.status);
  if (httpStatus == null || httpStatus < 400) {
    return null;
  }

  const body = getRecord(responseRecord?.data) ?? getRecord(errorRecord?.data);
  const validationErrors = getRecord(body?.errors);
  return {
    domainKey: null,
    errorCode: "http_error",
    i18nKey: null,
    severity: "error",
    userDisplayable: true,
    httpStatus,
    details: {
      errorRefs,
      status: httpStatus,
      title: firstString(body?.title, body?.message),
      errors: validationErrors,
      originalError: serializeUnknownError(error),
    },
  };
}
