import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionRoleControllerSuggestTransportMetadata } from "./staffPositionRoleControllerSuggestTransport.transport.generated";
import type { StaffPositionRoleSuggestionDto } from "../staffpositionroles/types/StaffPositionRoleSuggestionDto.generated";import type { SuggestStaffPositionRoleRequest } from "../staffpositionroles/types/SuggestStaffPositionRoleRequest.generated";
export const staffPositionRoleControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestStaffPositionRoleRequest; }, StaffPositionRoleSuggestionDto[]>({
  endpointKey: "get:/api/staffpositionroles/suggest/{field}",
  transportMetadata: staffPositionRoleControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
