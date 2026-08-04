import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionRoleControllerGetTransportMetadata } from "./staffPositionRoleControllerGetTransport.transport.generated";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";
export const staffPositionRoleControllerGetQuery = defineQueryBinding<{ id: string; }, StaffPositionRoleDto>({
  endpointKey: "get:/api/staffpositionroles/{id}",
  transportMetadata: staffPositionRoleControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.role.not_found"],
});
