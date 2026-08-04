import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentRevisionControllerCreateTransportMetadata } from "./documentRevisionControllerCreateTransport.transport.generated";
import type { CreateDocumentRevisionRequest } from "../documentrevisions/types/CreateDocumentRevisionRequest.generated";import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";
export const documentRevisionControllerCreateMutation = defineMutationBinding<CreateDocumentRevisionRequest, DocumentRevisionDto>({
  endpointKey: "post:/api/documentrevisions",
  transportMetadata: documentRevisionControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentrevisions", "get:/api/documentrevisions/lookup", "get:/api/documentrevisions/options/{field}", "get:/api/documentrevisions/suggest/{field}", "get:/api/documentrevisions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.revision.validation_failed"],
});
