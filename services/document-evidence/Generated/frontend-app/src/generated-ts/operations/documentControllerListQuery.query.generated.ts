import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentControllerListTransportMetadata } from "./documentControllerListTransport.transport.generated";
import type { ListDocumentRequest } from "../documents/types/ListDocumentRequest.generated";import type { ListDocumentResult } from "../documents/types/ListDocumentResult.generated";
export const documentControllerListQuery = defineQueryBinding<{ request: ListDocumentRequest; }, ListDocumentResult>({
  endpointKey: "get:/api/documents",
  transportMetadata: documentControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
