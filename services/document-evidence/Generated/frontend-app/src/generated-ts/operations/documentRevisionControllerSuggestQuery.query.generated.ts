import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentRevisionControllerSuggestTransportMetadata } from "./documentRevisionControllerSuggestTransport.transport.generated";
import type { DocumentRevisionSuggestionDto } from "../documentrevisions/types/DocumentRevisionSuggestionDto.generated";import type { SuggestDocumentRevisionRequest } from "../documentrevisions/types/SuggestDocumentRevisionRequest.generated";
export const documentRevisionControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestDocumentRevisionRequest; }, DocumentRevisionSuggestionDto[]>({
  endpointKey: "get:/api/documentrevisions/suggest/{field}",
  transportMetadata: documentRevisionControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
