import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionAssignmentControllerListTransportMetadata } from "./staffPositionAssignmentControllerListTransport.transport.generated";
import type { ListStaffPositionAssignmentRequest } from "../staffpositionassignments/types/ListStaffPositionAssignmentRequest.generated";import type { ListStaffPositionAssignmentResult } from "../staffpositionassignments/types/ListStaffPositionAssignmentResult.generated";
export const staffPositionAssignmentControllerListQuery = defineQueryBinding<{ request: ListStaffPositionAssignmentRequest; }, ListStaffPositionAssignmentResult>({
  endpointKey: "get:/api/staffpositionassignments",
  transportMetadata: staffPositionAssignmentControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
