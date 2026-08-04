import { defineMutationBinding } from "../runtime/mutationRuntime";
import { roleControllerDeleteTransportMetadata } from "./roleControllerDeleteTransport.transport.generated";

export const roleControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/roles/{id}",
  transportMetadata: roleControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/roles", "get:/api/roles/lookup", "get:/api/roles/options/{field}", "get:/api/roles/suggest/{field}", "get:/api/roles/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Role.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["role.not_found"],
});
