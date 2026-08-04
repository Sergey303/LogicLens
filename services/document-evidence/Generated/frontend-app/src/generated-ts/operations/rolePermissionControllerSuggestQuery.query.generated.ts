import { defineQueryBinding } from "../runtime/queryRuntime";
import { rolePermissionControllerSuggestTransportMetadata } from "./rolePermissionControllerSuggestTransport.transport.generated";
import type { RolePermissionSuggestionDto } from "../rolepermissions/types/RolePermissionSuggestionDto.generated";import type { SuggestRolePermissionRequest } from "../rolepermissions/types/SuggestRolePermissionRequest.generated";
export const rolePermissionControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestRolePermissionRequest; }, RolePermissionSuggestionDto[]>({
  endpointKey: "get:/api/rolepermissions/suggest/{field}",
  transportMetadata: rolePermissionControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
