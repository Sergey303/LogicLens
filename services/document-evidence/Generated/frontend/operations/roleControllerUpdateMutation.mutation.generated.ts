import { defineMutationBinding } from "../runtime/mutationRuntime";
import { roleControllerUpdateTransportMetadata } from "./roleControllerUpdateTransport.transport.generated";
import type { RoleDto } from "../roles/types/RoleDto.generated";import type { UpdateRoleRequest } from "../roles/types/UpdateRoleRequest.generated";
export const roleControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateRoleRequest; }, RoleDto>({
  endpointKey: "put:/api/roles/{id}",
  transportMetadata: roleControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/roles", "get:/api/roles/lookup", "get:/api/roles/options/{field}", "get:/api/roles/suggest/{field}", "get:/api/roles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.not_found", "role.validation_failed"],
});
