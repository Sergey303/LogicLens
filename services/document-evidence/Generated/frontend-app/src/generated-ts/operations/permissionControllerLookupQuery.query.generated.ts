import { defineQueryBinding } from "../runtime/queryRuntime";
import { permissionControllerLookupTransportMetadata } from "./permissionControllerLookupTransport.transport.generated";
import type { LookupPermissionRequest } from "../permissions/types/LookupPermissionRequest.generated";import type { PermissionLookupDto } from "../permissions/types/PermissionLookupDto.generated";
export const permissionControllerLookupQuery = defineQueryBinding<{ request: LookupPermissionRequest; }, PermissionLookupDto[]>({
  endpointKey: "get:/api/permissions/lookup",
  transportMetadata: permissionControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
