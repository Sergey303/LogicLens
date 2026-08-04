// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface ProcessingJobDto {
  "attempt": number;
  "documentRevisionId": string;
  "id": string;
  "idempotencyKey": string;
  "kind": string;
  "lastErrorCode"?: string | null;
  "leaseUntil"?: string | null;
  "state": string;
}
export const ProcessingJobDtoTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ProcessingJobDto" as const;

