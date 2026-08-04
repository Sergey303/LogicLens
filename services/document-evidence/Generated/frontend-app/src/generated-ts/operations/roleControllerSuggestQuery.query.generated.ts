import { defineQueryBinding } from "../runtime/queryRuntime";
import { roleControllerSuggestTransportMetadata } from "./roleControllerSuggestTransport.transport.generated";
import type { RoleSuggestionDto } from "../roles/types/RoleSuggestionDto.generated";import type { SuggestRoleRequest } from "../roles/types/SuggestRoleRequest.generated";
export const roleControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestRoleRequest; }, RoleSuggestionDto[]>({
  endpointKey: "get:/api/roles/suggest/{field}",
  transportMetadata: roleControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
