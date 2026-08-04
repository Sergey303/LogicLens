import { defineQueryBinding } from "../runtime/queryRuntime";
import { storedObjectControllerGetTransportMetadata } from "./storedObjectControllerGetTransport.transport.generated";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";
export const storedObjectControllerGetQuery = defineQueryBinding<{ id: string; }, StoredObjectDto>({
  endpointKey: "get:/api/storedobjects/{id}",
  transportMetadata: storedObjectControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["stored.object.not_found"],
});
