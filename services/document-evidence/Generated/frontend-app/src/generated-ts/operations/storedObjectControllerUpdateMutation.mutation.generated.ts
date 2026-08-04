import { defineMutationBinding } from "../runtime/mutationRuntime";
import { storedObjectControllerUpdateTransportMetadata } from "./storedObjectControllerUpdateTransport.transport.generated";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";import type { UpdateStoredObjectRequest } from "../storedobjects/types/UpdateStoredObjectRequest.generated";
export const storedObjectControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateStoredObjectRequest; }, StoredObjectDto>({
  endpointKey: "put:/api/storedobjects/{id}",
  transportMetadata: storedObjectControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/storedobjects", "get:/api/storedobjects/lookup", "get:/api/storedobjects/options/{field}", "get:/api/storedobjects/suggest/{field}", "get:/api/storedobjects/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["stored.object.not_found", "stored.object.validation_failed"],
});
