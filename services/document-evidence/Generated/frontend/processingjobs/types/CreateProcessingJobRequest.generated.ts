// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface CreateProcessingJobRequest {
  "attempt": number;
  "documentRevisionId": string;
  "idempotencyKey": string;
  "kind": string;
  "lastErrorCode"?: string | null;
  "leaseUntil"?: string | null;
  "state": string;
}
export const CreateProcessingJobRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.CreateProcessingJobRequest" as const;

