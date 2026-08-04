
import { inferDomainKey, isAcceptedErrorCode, normalizeSeverity, resolveErrorFamilyKey } from "./errorCodeRuntime";
import type { ParsedCanonicalError } from "./errorTypes";
import { compactDetails, firstBoolean, firstString, getRecord, serializeUnknownError, stringifyUnknown, toNumber } from "./errorValueUtils";

export function parseCanonicalError(error: unknown, errorRefs: readonly string[]): ParsedCanonicalError | null {
  return parseRestErrorCandidate(error, errorRefs)
    ?? parseRealtimeErrorCandidate(error, errorRefs)
    ?? parseLooseCodeCandidate(error, errorRefs);
}

function parseRestErrorCandidate(error: unknown, errorRefs: readonly string[]): ParsedCanonicalError | null {
  const responseRecord = getRecord(getRecord(error)?.response);
  const status = toNumber(responseRecord?.status) ?? toNumber(getRecord(error)?.status);
  const candidate = getRecord(responseRecord?.data) ?? getRecord(error);
  if (!candidate) {
    return null;
  }

  const extensions = getRecord(candidate.extensions);
  const errorRecord = getRecord(candidate.error);
  const errorCode = firstString(
    candidate.code, candidate.errorCode, errorRecord?.code, errorRecord?.errorCode, extensions?.code, extensions?.errorCode,
  );
  if (!isAcceptedErrorCode(errorCode, errorRefs)) {
    return null;
  }

  const familyKey = resolveErrorFamilyKey(errorCode);
  return {
    domainKey: firstString(candidate.domain, candidate.errorDomain, candidate.family, errorRecord?.domain, extensions?.domain, extensions?.errorDomain)
      ?? inferDomainKey(errorCode, familyKey),
    errorCode,
    errorFamilyKey: familyKey,
    details: compactDetails({
      message: firstString(candidate.title, errorRecord?.message),
      detail: firstString(candidate.detail, errorRecord?.details, stringifyUnknown(candidate.details)),
      errors: getRecord(candidate.errors),
      requestId: firstString(candidate.requestId, extensions?.requestId),
      operationId: firstString(candidate.operationId, extensions?.operationId),
      correlationId: firstString(candidate.correlationId, extensions?.correlationId),
      errorFamilyKey: familyKey,
    }),
    httpStatus: status,
    retryable: firstBoolean(candidate.retryable, candidate.isRetryable, errorRecord?.retryable),
    severity: normalizeSeverity(firstString(candidate.severity)),
    userDisplayable: firstBoolean(candidate.userDisplayable, candidate.isUserDisplayable, candidate.displayable),
  };
}

function parseRealtimeErrorCandidate(error: unknown, errorRefs: readonly string[]): ParsedCanonicalError | null {
  const candidate = getRecord(error) ?? getRecord(getRecord(error)?.data);
  const nestedError = getRecord(candidate?.error);
  const errorCode = firstString(candidate?.errorCode, nestedError?.code);
  if (!isAcceptedErrorCode(errorCode, errorRefs)) {
    return null;
  }

  const familyKey = resolveErrorFamilyKey(errorCode);
  return {
    domainKey: firstString(candidate?.errorDomain, nestedError?.domain) ?? inferDomainKey(errorCode, familyKey),
    errorCode,
    errorFamilyKey: familyKey,
    details: compactDetails({
      message: firstString(candidate?.message, nestedError?.message),
      detail: firstString(nestedError?.details, stringifyUnknown(candidate?.details)),
      requestId: firstString(candidate?.requestId),
      operationId: firstString(candidate?.operationId),
      correlationId: firstString(candidate?.correlationId),
      retryAfterMs: toNumber(nestedError?.retryAfterMs),
      errorFamilyKey: familyKey,
    }),
    retryable: firstBoolean(candidate?.retryable, nestedError?.retryable),
    severity: "error",
    userDisplayable: true,
  };
}

function parseLooseCodeCandidate(error: unknown, errorRefs: readonly string[]): ParsedCanonicalError | null {
  const record = getRecord(error);
  const errorCode = firstString(record?.errorCode, record?.code);
  if (!isAcceptedErrorCode(errorCode, errorRefs)) {
    return null;
  }

  const familyKey = resolveErrorFamilyKey(errorCode);
  return {
    domainKey: inferDomainKey(errorCode, familyKey),
    errorCode,
    errorFamilyKey: familyKey,
    details: compactDetails({
      errorFamilyKey: familyKey,
      originalError: serializeUnknownError(error),
    }),
    severity: "error",
    userDisplayable: true,
  };
}
