import { defineMutationBinding } from "../runtime/mutationRuntime";
import { processingJobControllerUpdateTransportMetadata } from "./processingJobControllerUpdateTransport.transport.generated";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";import type { UpdateProcessingJobRequest } from "../processingjobs/types/UpdateProcessingJobRequest.generated";
export const processingJobControllerUpdateMutation = defineMutationBinding<{ id: string; body: UpdateProcessingJobRequest; }, ProcessingJobDto>({
  endpointKey: "put:/api/processingjobs/{id}",
  transportMetadata: processingJobControllerUpdateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/processingjobs", "get:/api/processingjobs/lookup", "get:/api/processingjobs/options/{field}", "get:/api/processingjobs/suggest/{field}", "get:/api/processingjobs/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Update"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["processing.job.not_found", "processing.job.validation_failed"],
});
