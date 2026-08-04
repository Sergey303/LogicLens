import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionAssignmentControllerOptionsTransportMetadata } from "./staffPositionAssignmentControllerOptionsTransport.transport.generated";
import type { StaffPositionAssignmentOptionDto } from "../staffpositionassignments/types/StaffPositionAssignmentOptionDto.generated";
export const staffPositionAssignmentControllerOptionsQuery = defineQueryBinding<{ field: string; }, StaffPositionAssignmentOptionDto[]>({
  endpointKey: "get:/api/staffpositionassignments/options/{field}",
  transportMetadata: staffPositionAssignmentControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
