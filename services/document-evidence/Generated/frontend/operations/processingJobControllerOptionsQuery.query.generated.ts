import { defineQueryBinding } from "../runtime/queryRuntime";
import { processingJobControllerOptionsTransportMetadata } from "./processingJobControllerOptionsTransport.transport.generated";
import type { ProcessingJobOptionDto } from "../processingjobs/types/ProcessingJobOptionDto.generated";
export const processingJobControllerOptionsQuery = defineQueryBinding<{ field: string; }, ProcessingJobOptionDto[]>({
  endpointKey: "get:/api/processingjobs/options/{field}",
  transportMetadata: processingJobControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
