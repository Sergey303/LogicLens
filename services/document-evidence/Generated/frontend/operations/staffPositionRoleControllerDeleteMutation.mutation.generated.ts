import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionRoleControllerDeleteTransportMetadata } from "./staffPositionRoleControllerDeleteTransport.transport.generated";

export const staffPositionRoleControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/staffpositionroles/{id}",
  transportMetadata: staffPositionRoleControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositionroles", "get:/api/staffpositionroles/lookup", "get:/api/staffpositionroles/options/{field}", "get:/api/staffpositionroles/suggest/{field}", "get:/api/staffpositionroles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPositionRole.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.role.not_found"],
});
