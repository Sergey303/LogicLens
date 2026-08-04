import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentControllerDeleteTransportMetadata } from "./documentControllerDeleteTransport.transport.generated";

export const documentControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/documents/{id}",
  transportMetadata: documentControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documents", "get:/api/documents/lookup", "get:/api/documents/options/{field}", "get:/api/documents/suggest/{field}", "get:/api/documents/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Document.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.not_found"],
});
