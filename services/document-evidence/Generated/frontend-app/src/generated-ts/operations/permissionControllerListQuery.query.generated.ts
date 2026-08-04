import { defineQueryBinding } from "../runtime/queryRuntime";
import { permissionControllerListTransportMetadata } from "./permissionControllerListTransport.transport.generated";
import type { ListPermissionRequest } from "../permissions/types/ListPermissionRequest.generated";import type { ListPermissionResult } from "../permissions/types/ListPermissionResult.generated";
export const permissionControllerListQuery = defineQueryBinding<{ request: ListPermissionRequest; }, ListPermissionResult>({
  endpointKey: "get:/api/permissions",
  transportMetadata: permissionControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
