import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionAssignmentControllerGetTransportMetadata } from "./staffPositionAssignmentControllerGetTransport.transport.generated";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";
export const staffPositionAssignmentControllerGetQuery = defineQueryBinding<{ id: string; }, StaffPositionAssignmentDto>({
  endpointKey: "get:/api/staffpositionassignments/{id}",
  transportMetadata: staffPositionAssignmentControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.assignment.not_found"],
});
