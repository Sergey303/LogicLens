import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionRoleControllerUpdateTransportMetadata } from "./staffPositionRoleControllerUpdateTransport.transport.generated";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";import type { UpdateStaffPositionRoleRequest } from "../staffpositionroles/types/UpdateStaffPositionRoleRequest.generated";
export const staffPositionRoleControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateStaffPositionRoleRequest; }, StaffPositionRoleDto>({
  endpointKey: "put:/api/staffpositionroles/{id}",
  transportMetadata: staffPositionRoleControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionroles", "get:/api/staffpositionroles/lookup", "get:/api/staffpositionroles/options/{field}", "get:/api/staffpositionroles/suggest/{field}", "get:/api/staffpositionroles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.role.not_found", "staff.position.role.validation_failed"],
});
