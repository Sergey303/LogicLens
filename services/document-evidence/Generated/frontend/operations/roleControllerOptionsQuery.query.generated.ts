import { defineQueryBinding } from "../runtime/queryRuntime";
import { roleControllerOptionsTransportMetadata } from "./roleControllerOptionsTransport.transport.generated";
import type { RoleOptionDto } from "../roles/types/RoleOptionDto.generated";
export const roleControllerOptionsQuery = defineQueryBinding<{ field: string; }, RoleOptionDto[]>({
  endpointKey: "get:/api/roles/options/{field}",
  transportMetadata: roleControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
