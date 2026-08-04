import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionControllerSuggestTransportMetadata } from "./staffPositionControllerSuggestTransport.transport.generated";
import type { StaffPositionSuggestionDto } from "../staffpositions/types/StaffPositionSuggestionDto.generated";import type { SuggestStaffPositionRequest } from "../staffpositions/types/SuggestStaffPositionRequest.generated";
export const staffPositionControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestStaffPositionRequest; }, StaffPositionSuggestionDto[]>({
  endpointKey: "get:/api/staffpositions/suggest/{field}",
  transportMetadata: staffPositionControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
