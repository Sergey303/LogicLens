import { defineQueryBinding } from "../runtime/queryRuntime";
import { permissionControllerGetTransportMetadata } from "./permissionControllerGetTransport.transport.generated";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";
export const permissionControllerGetQuery = defineQueryBinding<{ id: string; }, PermissionDto>({
  endpointKey: "get:/api/permissions/{id}",
  transportMetadata: permissionControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["permission.not_found"],
});
