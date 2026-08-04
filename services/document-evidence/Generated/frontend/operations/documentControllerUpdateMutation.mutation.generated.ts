import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentControllerUpdateTransportMetadata } from "./documentControllerUpdateTransport.transport.generated";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";import type { UpdateDocumentRequest } from "../documents/types/UpdateDocumentRequest.generated";
export const documentControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateDocumentRequest; }, DocumentDto>({
  endpointKey: "put:/api/documents/{id}",
  transportMetadata: documentControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documents", "get:/api/documents/lookup", "get:/api/documents/options/{field}", "get:/api/documents/suggest/{field}", "get:/api/documents/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.not_found", "document.validation_failed"],
});
