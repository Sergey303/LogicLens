import { defineQueryBinding } from "../runtime/queryRuntime";
import { processingJobControllerLookupTransportMetadata } from "./processingJobControllerLookupTransport.transport.generated";
import type { LookupProcessingJobRequest } from "../processingjobs/types/LookupProcessingJobRequest.generated";import type { ProcessingJobLookupDto } from "../processingjobs/types/ProcessingJobLookupDto.generated";
export const processingJobControllerLookupQuery = defineQueryBinding<{ request: LookupProcessingJobRequest; }, ProcessingJobLookupDto[]>({
  endpointKey: "get:/api/processingjobs/lookup",
  transportMetadata: processingJobControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
