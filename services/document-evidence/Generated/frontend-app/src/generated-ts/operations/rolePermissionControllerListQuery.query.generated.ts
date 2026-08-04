import { defineQueryBinding } from "../runtime/queryRuntime";
import { rolePermissionControllerListTransportMetadata } from "./rolePermissionControllerListTransport.transport.generated";
import type { ListRolePermissionRequest } from "../rolepermissions/types/ListRolePermissionRequest.generated";import type { ListRolePermissionResult } from "../rolepermissions/types/ListRolePermissionResult.generated";
export const rolePermissionControllerListQuery = defineQueryBinding<{ request: ListRolePermissionRequest; }, ListRolePermissionResult>({
  endpointKey: "get:/api/rolepermissions",
  transportMetadata: rolePermissionControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
