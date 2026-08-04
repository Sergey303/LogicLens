import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentRevisionControllerLookupTransportMetadata } from "./documentRevisionControllerLookupTransport.transport.generated";
import type { DocumentRevisionLookupDto } from "../documentrevisions/types/DocumentRevisionLookupDto.generated";import type { LookupDocumentRevisionRequest } from "../documentrevisions/types/LookupDocumentRevisionRequest.generated";
export const documentRevisionControllerLookupQuery = defineQueryBinding<{ request: LookupDocumentRevisionRequest; }, DocumentRevisionLookupDto[]>({
  endpointKey: "get:/api/documentrevisions/lookup",
  transportMetadata: documentRevisionControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
