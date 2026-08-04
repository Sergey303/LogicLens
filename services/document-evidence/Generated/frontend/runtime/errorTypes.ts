
export interface FrontendDomainError {
  domainKey: string | null;
  errorCode: string;
  i18nKey: string | null;
  severity: "error" | "warning" | "info";
  userDisplayable: boolean;
  details?: Record<string, unknown>;
  httpStatus?: number;
  retryable?: boolean;
}

export interface ErrorCatalogRef {
  errorFamilyKey: string;
  errorCode: string;
}

export interface RestErrorEnvelope {
  domain?: string;
  errorDomain?: string;
  family?: string;
  code?: string;
  errorCode?: string;
  userDisplayable?: boolean;
  isUserDisplayable?: boolean;
  displayable?: boolean;
  retryable?: boolean;
  isRetryable?: boolean;
  severity?: string;
  details?: unknown;
  detail?: unknown;
  requestId?: string;
  operationId?: string;
  correlationId?: string;
  status?: number;
  title?: string;
  type?: string;
  extensions?: Record<string, unknown>;
}

export interface RealtimeErrorEnvelope {
  requestId?: string;
  operationId?: string;
  correlationId?: string;
  error?: {
    domain?: string;
    code?: string;
    retryable?: boolean;
    retryAfterMs?: number;
    details?: unknown;
    message?: string;
  };
}

export type FrontendErrorSeverity = FrontendDomainError["severity"];

export interface ParsedCanonicalError {
  domainKey: string | null;
  errorCode: string;
  errorFamilyKey: string | null;
  details?: Record<string, unknown>;
  httpStatus?: number;
  retryable?: boolean;
  severity?: FrontendErrorSeverity;
  userDisplayable?: boolean;
}
