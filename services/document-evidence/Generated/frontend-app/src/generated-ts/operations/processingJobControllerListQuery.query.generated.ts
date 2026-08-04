import { defineQueryBinding } from "../runtime/queryRuntime";
import { processingJobControllerListTransportMetadata } from "./processingJobControllerListTransport.transport.generated";
import type { ListProcessingJobRequest } from "../processingjobs/types/ListProcessingJobRequest.generated";import type { ListProcessingJobResult } from "../processingjobs/types/ListProcessingJobResult.generated";
export const processingJobControllerListQuery = defineQueryBinding<{ request: ListProcessingJobRequest; }, ListProcessingJobResult>({
  endpointKey: "get:/api/processingjobs",
  transportMetadata: processingJobControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
