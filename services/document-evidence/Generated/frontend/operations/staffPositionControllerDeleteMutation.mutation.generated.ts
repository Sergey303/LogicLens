import { defineMutationBinding } from "../runtime/mutationRuntime";
import { staffPositionControllerDeleteTransportMetadata } from "./staffPositionControllerDeleteTransport.transport.generated";

export const staffPositionControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/staffpositions/{id}",
  transportMetadata: staffPositionControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/staffpositions", "get:/api/staffpositions/lookup", "get:/api/staffpositions/options/{field}", "get:/api/staffpositions/suggest/{field}", "get:/api/staffpositions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["staff.position.not_found"],
});
