import { defineQueryBinding } from "../runtime/queryRuntime";
import { processingJobControllerGetTransportMetadata } from "./processingJobControllerGetTransport.transport.generated";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";
export const processingJobControllerGetQuery = defineQueryBinding<{ id: string; }, ProcessingJobDto>({
  endpointKey: "get:/api/processingjobs/{id}",
  transportMetadata: processingJobControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["processing.job.not_found"],
});
