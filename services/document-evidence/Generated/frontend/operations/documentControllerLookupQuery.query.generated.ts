import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentControllerLookupTransportMetadata } from "./documentControllerLookupTransport.transport.generated";
import type { DocumentLookupDto } from "../documents/types/DocumentLookupDto.generated";import type { LookupDocumentRequest } from "../documents/types/LookupDocumentRequest.generated";
export const documentControllerLookupQuery = defineQueryBinding<{ request: LookupDocumentRequest; }, DocumentLookupDto[]>({
  endpointKey: "get:/api/documents/lookup",
  transportMetadata: documentControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
