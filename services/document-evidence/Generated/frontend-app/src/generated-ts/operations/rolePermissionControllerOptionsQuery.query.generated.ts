import { defineQueryBinding } from "../runtime/queryRuntime";
import { rolePermissionControllerOptionsTransportMetadata } from "./rolePermissionControllerOptionsTransport.transport.generated";
import type { RolePermissionOptionDto } from "../rolepermissions/types/RolePermissionOptionDto.generated";
export const rolePermissionControllerOptionsQuery = defineQueryBinding<{ field: string; }, RolePermissionOptionDto[]>({
  endpointKey: "get:/api/rolepermissions/options/{field}",
  transportMetadata: rolePermissionControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
