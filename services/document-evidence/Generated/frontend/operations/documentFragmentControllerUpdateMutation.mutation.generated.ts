import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentFragmentControllerUpdateTransportMetadata } from "./documentFragmentControllerUpdateTransport.transport.generated";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";import type { UpdateDocumentFragmentRequest } from "../documentfragments/types/UpdateDocumentFragmentRequest.generated";
export const documentFragmentControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateDocumentFragmentRequest; }, DocumentFragmentDto>({
  endpointKey: "put:/api/documentfragments/{id}",
  transportMetadata: documentFragmentControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentfragments", "get:/api/documentfragments/lookup", "get:/api/documentfragments/options/{field}", "get:/api/documentfragments/suggest/{field}", "get:/api/documentfragments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.fragment.not_found", "document.fragment.validation_failed"],
});
