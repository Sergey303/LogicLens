import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionAssignmentControllerLookupTransportMetadata } from "./staffPositionAssignmentControllerLookupTransport.transport.generated";
import type { LookupStaffPositionAssignmentRequest } from "../staffpositionassignments/types/LookupStaffPositionAssignmentRequest.generated";import type { StaffPositionAssignmentLookupDto } from "../staffpositionassignments/types/StaffPositionAssignmentLookupDto.generated";
export const staffPositionAssignmentControllerLookupQuery = defineQueryBinding<{ request: LookupStaffPositionAssignmentRequest; }, StaffPositionAssignmentLookupDto[]>({
  endpointKey: "get:/api/staffpositionassignments/lookup",
  transportMetadata: staffPositionAssignmentControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
