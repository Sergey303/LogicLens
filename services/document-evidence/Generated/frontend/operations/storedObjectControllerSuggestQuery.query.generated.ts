import { defineQueryBinding } from "../runtime/queryRuntime";
import { storedObjectControllerSuggestTransportMetadata } from "./storedObjectControllerSuggestTransport.transport.generated";
import type { StoredObjectSuggestionDto } from "../storedobjects/types/StoredObjectSuggestionDto.generated";import type { SuggestStoredObjectRequest } from "../storedobjects/types/SuggestStoredObjectRequest.generated";
export const storedObjectControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestStoredObjectRequest; }, StoredObjectSuggestionDto[]>({
  endpointKey: "get:/api/storedobjects/suggest/{field}",
  transportMetadata: storedObjectControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StoredObject.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
