import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentFragmentControllerDeleteTransportMetadata } from "./documentFragmentControllerDeleteTransport.transport.generated";

export const documentFragmentControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/documentfragments/{id}",
  transportMetadata: documentFragmentControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentfragments", "get:/api/documentfragments/lookup", "get:/api/documentfragments/options/{field}", "get:/api/documentfragments/suggest/{field}", "get:/api/documentfragments/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.fragment.not_found"],
});
