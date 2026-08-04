import { defineQueryBinding } from "../runtime/queryRuntime";
import { rolePermissionControllerGetTransportMetadata } from "./rolePermissionControllerGetTransport.transport.generated";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";
export const rolePermissionControllerGetQuery = defineQueryBinding<{ id: string; }, RolePermissionDto>({
  endpointKey: "get:/api/rolepermissions/{id}",
  transportMetadata: rolePermissionControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.permission.not_found"],
});
