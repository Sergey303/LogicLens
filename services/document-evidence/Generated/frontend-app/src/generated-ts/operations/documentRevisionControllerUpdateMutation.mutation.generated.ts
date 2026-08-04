import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentRevisionControllerUpdateTransportMetadata } from "./documentRevisionControllerUpdateTransport.transport.generated";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";import type { UpdateDocumentRevisionRequest } from "../documentrevisions/types/UpdateDocumentRevisionRequest.generated";
export const documentRevisionControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateDocumentRevisionRequest; }, DocumentRevisionDto>({
  endpointKey: "put:/api/documentrevisions/{id}",
  transportMetadata: documentRevisionControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentrevisions", "get:/api/documentrevisions/lookup", "get:/api/documentrevisions/options/{field}", "get:/api/documentrevisions/suggest/{field}", "get:/api/documentrevisions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.revision.not_found", "document.revision.validation_failed"],
});
