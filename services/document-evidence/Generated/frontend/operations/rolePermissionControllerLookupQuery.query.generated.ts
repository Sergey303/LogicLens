import { defineQueryBinding } from "../runtime/queryRuntime";
import { rolePermissionControllerLookupTransportMetadata } from "./rolePermissionControllerLookupTransport.transport.generated";
import type { LookupRolePermissionRequest } from "../rolepermissions/types/LookupRolePermissionRequest.generated";import type { RolePermissionLookupDto } from "../rolepermissions/types/RolePermissionLookupDto.generated";
export const rolePermissionControllerLookupQuery = defineQueryBinding<{ request: LookupRolePermissionRequest; }, RolePermissionLookupDto[]>({
  endpointKey: "get:/api/rolepermissions/lookup",
  transportMetadata: rolePermissionControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
