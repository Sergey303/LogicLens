import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionRoleControllerOptionsTransportMetadata } from "./staffPositionRoleControllerOptionsTransport.transport.generated";
import type { StaffPositionRoleOptionDto } from "../staffpositionroles/types/StaffPositionRoleOptionDto.generated";
export const staffPositionRoleControllerOptionsQuery = defineQueryBinding<{ field: string; }, StaffPositionRoleOptionDto[]>({
  endpointKey: "get:/api/staffpositionroles/options/{field}",
  transportMetadata: staffPositionRoleControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
