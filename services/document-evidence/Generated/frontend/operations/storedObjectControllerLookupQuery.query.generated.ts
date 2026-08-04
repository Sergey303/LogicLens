import { defineQueryBinding } from "../runtime/queryRuntime";
import { storedObjectControllerLookupTransportMetadata } from "./storedObjectControllerLookupTransport.transport.generated";
import type { LookupStoredObjectRequest } from "../storedobjects/types/LookupStoredObjectRequest.generated";import type { StoredObjectLookupDto } from "../storedobjects/types/StoredObjectLookupDto.generated";
export const storedObjectControllerLookupQuery = defineQueryBinding<{ request: LookupStoredObjectRequest; }, StoredObjectLookupDto[]>({
  endpointKey: "get:/api/storedobjects/lookup",
  transportMetadata: storedObjectControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
