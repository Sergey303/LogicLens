import { defineQueryBinding } from "../runtime/queryRuntime";
import { permissionControllerOptionsTransportMetadata } from "./permissionControllerOptionsTransport.transport.generated";
import type { PermissionOptionDto } from "../permissions/types/PermissionOptionDto.generated";
export const permissionControllerOptionsQuery = defineQueryBinding<{ field: string; }, PermissionOptionDto[]>({
  endpointKey: "get:/api/permissions/options/{field}",
  transportMetadata: permissionControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
