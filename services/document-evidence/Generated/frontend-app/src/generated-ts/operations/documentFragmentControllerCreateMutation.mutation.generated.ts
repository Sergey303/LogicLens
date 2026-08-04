import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentFragmentControllerCreateTransportMetadata } from "./documentFragmentControllerCreateTransport.transport.generated";
import type { CreateDocumentFragmentRequest } from "../documentfragments/types/CreateDocumentFragmentRequest.generated";import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";
export const documentFragmentControllerCreateMutation = defineMutationBinding<CreateDocumentFragmentRequest, DocumentFragmentDto>({
  endpointKey: "post:/api/documentfragments",
  transportMetadata: documentFragmentControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentfragments", "get:/api/documentfragments/lookup", "get:/api/documentfragments/options/{field}", "get:/api/documentfragments/suggest/{field}", "get:/api/documentfragments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.fragment.validation_failed"],
});
