import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentRevisionControllerListTransportMetadata } from "./documentRevisionControllerListTransport.transport.generated";
import type { ListDocumentRevisionRequest } from "../documentrevisions/types/ListDocumentRevisionRequest.generated";import type { ListDocumentRevisionResult } from "../documentrevisions/types/ListDocumentRevisionResult.generated";
export const documentRevisionControllerListQuery = defineQueryBinding<{ request: ListDocumentRevisionRequest; }, ListDocumentRevisionResult>({
  endpointKey: "get:/api/documentrevisions",
  transportMetadata: documentRevisionControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
