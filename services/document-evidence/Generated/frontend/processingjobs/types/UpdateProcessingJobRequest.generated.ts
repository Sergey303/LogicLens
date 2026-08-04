// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface UpdateProcessingJobRequest {
  "attempt": number;
  "documentRevisionId": string;
  "idempotencyKey": string;
  "kind": string;
  "lastErrorCode"?: string | null;
  "leaseUntil"?: string | null;
  "state": string;
}
export const UpdateProcessingJobRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.UpdateProcessingJobRequest" as const;

