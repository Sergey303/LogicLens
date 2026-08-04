import { defineQueryBinding } from "../runtime/queryRuntime";
import { roleControllerLookupTransportMetadata } from "./roleControllerLookupTransport.transport.generated";
import type { LookupRoleRequest } from "../roles/types/LookupRoleRequest.generated";import type { RoleLookupDto } from "../roles/types/RoleLookupDto.generated";
export const roleControllerLookupQuery = defineQueryBinding<{ request: LookupRoleRequest; }, RoleLookupDto[]>({
  endpointKey: "get:/api/roles/lookup",
  transportMetadata: roleControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
