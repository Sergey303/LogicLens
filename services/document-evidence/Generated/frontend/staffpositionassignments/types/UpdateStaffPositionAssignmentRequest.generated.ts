// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export interface UpdateStaffPositionAssignmentRequest {
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
export const UpdateStaffPositionAssignmentRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.UpdateStaffPositionAssignmentRequest" as const;

