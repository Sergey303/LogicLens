import { defineMutationBinding } from "../runtime/mutationRuntime";
import { permissionControllerCreateTransportMetadata } from "./permissionControllerCreateTransport.transport.generated";
import type { CreatePermissionRequest } from "../permissions/types/CreatePermissionRequest.generated";import type { PermissionDto } from "../permissions/types/PermissionDto.generated";
export const permissionControllerCreateMutation = defineMutationBinding<CreatePermissionRequest, PermissionDto>({
  endpointKey: "post:/api/permissions",
  transportMetadata: permissionControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/permissions", "get:/api/permissions/lookup", "get:/api/permissions/options/{field}", "get:/api/permissions/suggest/{field}", "get:/api/permissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["permission.validation_failed"],
});
