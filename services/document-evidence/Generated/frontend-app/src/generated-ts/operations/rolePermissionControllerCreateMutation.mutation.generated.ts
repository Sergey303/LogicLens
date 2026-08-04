import { defineMutationBinding } from "../runtime/mutationRuntime";
import { rolePermissionControllerCreateTransportMetadata } from "./rolePermissionControllerCreateTransport.transport.generated";
import type { CreateRolePermissionRequest } from "../rolepermissions/types/CreateRolePermissionRequest.generated";import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";
export const rolePermissionControllerCreateMutation = defineMutationBinding<CreateRolePermissionRequest, RolePermissionDto>({
  endpointKey: "post:/api/rolepermissions",
  transportMetadata: rolePermissionControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/rolepermissions", "get:/api/rolepermissions/lookup", "get:/api/rolepermissions/options/{field}", "get:/api/rolepermissions/suggest/{field}", "get:/api/rolepermissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.permission.validation_failed"],
});
