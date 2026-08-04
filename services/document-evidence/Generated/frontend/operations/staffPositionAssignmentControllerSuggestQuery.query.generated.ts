import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionAssignmentControllerSuggestTransportMetadata } from "./staffPositionAssignmentControllerSuggestTransport.transport.generated";
import type { StaffPositionAssignmentSuggestionDto } from "../staffpositionassignments/types/StaffPositionAssignmentSuggestionDto.generated";import type { SuggestStaffPositionAssignmentRequest } from "../staffpositionassignments/types/SuggestStaffPositionAssignmentRequest.generated";
export const staffPositionAssignmentControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestStaffPositionAssignmentRequest; }, StaffPositionAssignmentSuggestionDto[]>({
  endpointKey: "get:/api/staffpositionassignments/suggest/{field}",
  transportMetadata: staffPositionAssignmentControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionAssignment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
