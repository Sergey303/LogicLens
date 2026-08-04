import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentControllerCreateTransportMetadata } from "./documentControllerCreateTransport.transport.generated";
import type { CreateDocumentRequest } from "../documents/types/CreateDocumentRequest.generated";import type { DocumentDto } from "../documents/types/DocumentDto.generated";
export const documentControllerCreateMutation = defineMutationBinding<CreateDocumentRequest, DocumentDto>({
  endpointKey: "post:/api/documents",
  transportMetadata: documentControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documents", "get:/api/documents/lookup", "get:/api/documents/options/{field}", "get:/api/documents/suggest/{field}", "get:/api/documents/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.validation_failed"],
});
