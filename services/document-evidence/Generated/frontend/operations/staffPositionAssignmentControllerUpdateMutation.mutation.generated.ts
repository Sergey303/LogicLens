import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionAssignmentControllerUpdateTransportMetadata } from "./staffPositionAssignmentControllerUpdateTransport.transport.generated";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";import type { UpdateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/UpdateStaffPositionAssignmentRequest.generated";
export const staffPositionAssignmentControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateStaffPositionAssignmentRequest; }, StaffPositionAssignmentDto>({
  endpointKey: "put:/api/staffpositionassignments/{id}",
  transportMetadata: staffPositionAssignmentControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionassignments", "get:/api/staffpositionassignments/lookup", "get:/api/staffpositionassignments/options/{field}", "get:/api/staffpositionassignments/suggest/{field}", "get:/api/staffpositionassignments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.assignment.not_found", "staff.position.assignment.validation_failed"],
});
