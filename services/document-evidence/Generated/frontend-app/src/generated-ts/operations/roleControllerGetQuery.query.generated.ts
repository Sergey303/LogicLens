import { defineQueryBinding } from "../runtime/queryRuntime";
import { roleControllerGetTransportMetadata } from "./roleControllerGetTransport.transport.generated";
import type { RoleDto } from "../roles/types/RoleDto.generated";
export const roleControllerGetQuery = defineQueryBinding<{ id: string; }, RoleDto>({
  endpointKey: "get:/api/roles/{id}",
  transportMetadata: roleControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.not_found"],
});
