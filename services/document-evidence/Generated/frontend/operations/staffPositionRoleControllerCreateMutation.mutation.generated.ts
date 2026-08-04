import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionRoleControllerCreateTransportMetadata } from "./staffPositionRoleControllerCreateTransport.transport.generated";
import type { CreateStaffPositionRoleRequest } from "../staffpositionroles/types/CreateStaffPositionRoleRequest.generated";import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";
export const staffPositionRoleControllerCreateMutation = defineMutationBinding<CreateStaffPositionRoleRequest, StaffPositionRoleDto>({
  endpointKey: "post:/api/staffpositionroles",
  transportMetadata: staffPositionRoleControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionroles", "get:/api/staffpositionroles/lookup", "get:/api/staffpositionroles/options/{field}", "get:/api/staffpositionroles/suggest/{field}", "get:/api/staffpositionroles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.role.validation_failed"],
});
