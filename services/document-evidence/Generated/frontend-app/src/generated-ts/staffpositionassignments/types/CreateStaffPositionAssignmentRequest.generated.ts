// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface CreateStaffPositionAssignmentRequest {
  "assignmentKind": string;
  "endsAt"?: string | null;
  "endsAtUtc"?: string | null;
  "isActive": boolean;
  "reason"?: string | null;
  "staffPositionId": string;
  "startsAt": string;
  "startsAtUtc": string;
  "userId": string;
}
export const CreateStaffPositionAssignmentRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.CreateStaffPositionAssignmentRequest" as const;

