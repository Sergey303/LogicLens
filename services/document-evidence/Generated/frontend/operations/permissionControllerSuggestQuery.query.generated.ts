import { defineQueryBinding } from "../runtime/queryRuntime";
import { permissionControllerSuggestTransportMetadata } from "./permissionControllerSuggestTransport.transport.generated";
import type { PermissionSuggestionDto } from "../permissions/types/PermissionSuggestionDto.generated";import type { SuggestPermissionRequest } from "../permissions/types/SuggestPermissionRequest.generated";
export const permissionControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestPermissionRequest; }, PermissionSuggestionDto[]>({
  endpointKey: "get:/api/permissions/suggest/{field}",
  transportMetadata: permissionControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
