import { defineMutationBinding } from "../runtime/mutationRuntime";
import { processingJobControllerDeleteTransportMetadata } from "./processingJobControllerDeleteTransport.transport.generated";

export const processingJobControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/processingjobs/{id}",
  transportMetadata: processingJobControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/processingjobs", "get:/api/processingjobs/lookup", "get:/api/processingjobs/options/{field}", "get:/api/processingjobs/suggest/{field}", "get:/api/processingjobs/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["processing.job.not_found"],
});
