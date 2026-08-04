import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionAssignmentControllerCreateTransportMetadata } from "./staffPositionAssignmentControllerCreateTransport.transport.generated";
import type { CreateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/CreateStaffPositionAssignmentRequest.generated";import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";
export const staffPositionAssignmentControllerCreateMutation = defineMutationBinding<CreateStaffPositionAssignmentRequest, StaffPositionAssignmentDto>({
  endpointKey: "post:/api/staffpositionassignments",
  transportMetadata: staffPositionAssignmentControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionassignments", "get:/api/staffpositionassignments/lookup", "get:/api/staffpositionassignments/options/{field}", "get:/api/staffpositionassignments/suggest/{field}", "get:/api/staffpositionassignments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.assignment.validation_failed"],
});
