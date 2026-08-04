import { defineQueryBinding } from "../runtime/queryRuntime";
import { storedObjectControllerListTransportMetadata } from "./storedObjectControllerListTransport.transport.generated";
import type { ListStoredObjectRequest } from "../storedobjects/types/ListStoredObjectRequest.generated";import type { ListStoredObjectResult } from "../storedobjects/types/ListStoredObjectResult.generated";
export const storedObjectControllerListQuery = defineQueryBinding<{ request: ListStoredObjectRequest; }, ListStoredObjectResult>({
  endpointKey: "get:/api/storedobjects",
  transportMetadata: storedObjectControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
