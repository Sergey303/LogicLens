import { defineMutationBinding } from "../runtime/mutationRuntime";
import { permissionControllerUpdateTransportMetadata } from "./permissionControllerUpdateTransport.transport.generated";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";import type { UpdatePermissionRequest } from "../permissions/types/UpdatePermissionRequest.generated";
export const permissionControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdatePermissionRequest; }, PermissionDto>({
  endpointKey: "put:/api/permissions/{id}",
  transportMetadata: permissionControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/permissions", "get:/api/permissions/lookup", "get:/api/permissions/options/{field}", "get:/api/permissions/suggest/{field}", "get:/api/permissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["permission.not_found", "permission.validation_failed"],
});
