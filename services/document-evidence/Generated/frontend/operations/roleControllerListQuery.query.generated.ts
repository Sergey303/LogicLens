import { defineQueryBinding } from "../runtime/queryRuntime";
import { roleControllerListTransportMetadata } from "./roleControllerListTransport.transport.generated";
import type { ListRoleRequest } from "../roles/types/ListRoleRequest.generated";import type { ListRoleResult } from "../roles/types/ListRoleResult.generated";
export const roleControllerListQuery = defineQueryBinding<{ request: ListRoleRequest; }, ListRoleResult>({
  endpointKey: "get:/api/roles",
  transportMetadata: roleControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
