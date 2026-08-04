import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentControllerSuggestTransportMetadata } from "./documentControllerSuggestTransport.transport.generated";
import type { DocumentSuggestionDto } from "../documents/types/DocumentSuggestionDto.generated";import type { SuggestDocumentRequest } from "../documents/types/SuggestDocumentRequest.generated";
export const documentControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestDocumentRequest; }, DocumentSuggestionDto[]>({
  endpointKey: "get:/api/documents/suggest/{field}",
  transportMetadata: documentControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
