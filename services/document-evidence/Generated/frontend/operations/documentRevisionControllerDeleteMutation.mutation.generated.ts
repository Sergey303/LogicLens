import { defineMutationBinding } from "../runtime/mutationRuntime";
import { documentRevisionControllerDeleteTransportMetadata } from "./documentRevisionControllerDeleteTransport.transport.generated";

export const documentRevisionControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/documentrevisions/{id}",
  transportMetadata: documentRevisionControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/documentrevisions", "get:/api/documentrevisions/lookup", "get:/api/documentrevisions/options/{field}", "get:/api/documentrevisions/suggest/{field}", "get:/api/documentrevisions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentRevision.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.revision.not_found"],
});
