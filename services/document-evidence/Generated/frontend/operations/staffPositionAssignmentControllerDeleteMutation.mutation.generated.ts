import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionAssignmentControllerDeleteTransportMetadata } from "./staffPositionAssignmentControllerDeleteTransport.transport.generated";

export const staffPositionAssignmentControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/staffpositionassignments/{id}",
  transportMetadata: staffPositionAssignmentControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionassignments", "get:/api/staffpositionassignments/lookup", "get:/api/staffpositionassignments/options/{field}", "get:/api/staffpositionassignments/suggest/{field}", "get:/api/staffpositionassignments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.assignment.not_found"],
});
