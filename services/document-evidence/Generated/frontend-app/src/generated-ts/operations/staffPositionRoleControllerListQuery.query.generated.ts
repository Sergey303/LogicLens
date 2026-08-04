import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionRoleControllerListTransportMetadata } from "./staffPositionRoleControllerListTransport.transport.generated";
import type { ListStaffPositionRoleRequest } from "../staffpositionroles/types/ListStaffPositionRoleRequest.generated";import type { ListStaffPositionRoleResult } from "../staffpositionroles/types/ListStaffPositionRoleResult.generated";
export const staffPositionRoleControllerListQuery = defineQueryBinding<{ request: ListStaffPositionRoleRequest; }, ListStaffPositionRoleResult>({
  endpointKey: "get:/api/staffpositionroles",
  transportMetadata: staffPositionRoleControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
