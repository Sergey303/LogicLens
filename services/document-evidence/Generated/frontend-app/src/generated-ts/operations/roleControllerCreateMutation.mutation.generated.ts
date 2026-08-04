import { defineMutationBinding } from "../runtime/mutationRuntime";
import { roleControllerCreateTransportMetadata } from "./roleControllerCreateTransport.transport.generated";
import type { CreateRoleRequest } from "../roles/types/CreateRoleRequest.generated";import type { RoleDto } from "../roles/types/RoleDto.generated";
export const roleControllerCreateMutation = defineMutationBinding<CreateRoleRequest, RoleDto>({
  endpointKey: "post:/api/roles",
  transportMetadata: roleControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/roles", "get:/api/roles/lookup", "get:/api/roles/options/{field}", "get:/api/roles/suggest/{field}", "get:/api/roles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.validation_failed"],
});
