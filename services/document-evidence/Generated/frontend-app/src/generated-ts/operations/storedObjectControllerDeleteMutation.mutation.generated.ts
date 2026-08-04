import { defineMutationBinding } from "../runtime/mutationRuntime";
import { storedObjectControllerDeleteTransportMetadata } from "./storedObjectControllerDeleteTransport.transport.generated";

export const storedObjectControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/storedobjects/{id}",
  transportMetadata: storedObjectControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/storedobjects", "get:/api/storedobjects/lookup", "get:/api/storedobjects/options/{field}", "get:/api/storedobjects/suggest/{field}", "get:/api/storedobjects/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["stored.object.not_found"],
});
