import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionRoleControllerLookupTransportMetadata } from "./staffPositionRoleControllerLookupTransport.transport.generated";
import type { LookupStaffPositionRoleRequest } from "../staffpositionroles/types/LookupStaffPositionRoleRequest.generated";import type { StaffPositionRoleLookupDto } from "../staffpositionroles/types/StaffPositionRoleLookupDto.generated";
export const staffPositionRoleControllerLookupQuery = defineQueryBinding<{ request: LookupStaffPositionRoleRequest; }, StaffPositionRoleLookupDto[]>({
  endpointKey: "get:/api/staffpositionroles/lookup",
  transportMetadata: staffPositionRoleControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
