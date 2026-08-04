import { defineMutationBinding } from "../runtime/mutationRuntime";
import { rolePermissionControllerDeleteTransportMetadata } from "./rolePermissionControllerDeleteTransport.transport.generated";

export const rolePermissionControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/rolepermissions/{id}",
  transportMetadata: rolePermissionControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/rolepermissions", "get:/api/rolepermissions/lookup", "get:/api/rolepermissions/options/{field}", "get:/api/rolepermissions/suggest/{field}", "get:/api/rolepermissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["RolePermission.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.permission.not_found"],
});
