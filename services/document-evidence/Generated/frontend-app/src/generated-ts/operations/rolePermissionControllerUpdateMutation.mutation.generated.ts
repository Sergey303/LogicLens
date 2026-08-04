import { defineMutationBinding } from "../runtime/mutationRuntime";
import { rolePermissionControllerUpdateTransportMetadata } from "./rolePermissionControllerUpdateTransport.transport.generated";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";import type { UpdateRolePermissionRequest } from "../rolepermissions/types/UpdateRolePermissionRequest.generated";
export const rolePermissionControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateRolePermissionRequest; }, RolePermissionDto>({
  endpointKey: "put:/api/rolepermissions/{id}",
  transportMetadata: rolePermissionControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/rolepermissions", "get:/api/rolepermissions/lookup", "get:/api/rolepermissions/options/{field}", "get:/api/rolepermissions/suggest/{field}", "get:/api/rolepermissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.permission.not_found", "role.permission.validation_failed"],
});
