import { defineMutationBinding } from "../runtime/mutationRuntime";
import { processingJobControllerCreateTransportMetadata } from "./processingJobControllerCreateTransport.transport.generated";
import type { CreateProcessingJobRequest } from "../processingjobs/types/CreateProcessingJobRequest.generated";import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";
export const processingJobControllerCreateMutation = defineMutationBinding<CreateProcessingJobRequest, ProcessingJobDto>({
  endpointKey: "post:/api/processingjobs",
  transportMetadata: processingJobControllerCreateTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/processingjobs", "get:/api/processingjobs/lookup", "get:/api/processingjobs/options/{field}", "get:/api/processingjobs/suggest/{field}", "get:/api/processingjobs/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Create"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["processing.job.validation_failed"],
});
