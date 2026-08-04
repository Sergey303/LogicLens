import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentFragmentControllerSuggestTransportMetadata } from "./documentFragmentControllerSuggestTransport.transport.generated";
import type { DocumentFragmentSuggestionDto } from "../documentfragments/types/DocumentFragmentSuggestionDto.generated";import type { SuggestDocumentFragmentRequest } from "../documentfragments/types/SuggestDocumentFragmentRequest.generated";
export const documentFragmentControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestDocumentFragmentRequest; }, DocumentFragmentSuggestionDto[]>({
  endpointKey: "get:/api/documentfragments/suggest/{field}",
  transportMetadata: documentFragmentControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
