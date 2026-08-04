import { defineMutationBinding } from "../runtime/mutationRuntime";
import { storedObjectControllerCreateTransportMetadata } from "./storedObjectControllerCreateTransport.transport.generated";
import type { CreateStoredObjectRequest } from "../storedobjects/types/CreateStoredObjectRequest.generated";import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";
export const storedObjectControllerCreateMutation = defineMutationBinding<CreateStoredObjectRequest, StoredObjectDto>({
  endpointKey: "post:/api/storedobjects",
  transportMetadata: storedObjectControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/storedobjects", "get:/api/storedobjects/lookup", "get:/api/storedobjects/options/{field}", "get:/api/storedobjects/suggest/{field}", "get:/api/storedobjects/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["stored.object.validation_failed"],
});
