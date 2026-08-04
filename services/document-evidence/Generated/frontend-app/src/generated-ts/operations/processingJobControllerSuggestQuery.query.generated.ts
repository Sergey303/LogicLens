import { defineQueryBinding } from "../runtime/queryRuntime";
import { processingJobControllerSuggestTransportMetadata } from "./processingJobControllerSuggestTransport.transport.generated";
import type { ProcessingJobSuggestionDto } from "../processingjobs/types/ProcessingJobSuggestionDto.generated";import type { SuggestProcessingJobRequest } from "../processingjobs/types/SuggestProcessingJobRequest.generated";
export const processingJobControllerSuggestQuery = defineQueryBinding<{ field: string; request: SuggestProcessingJobRequest; }, ProcessingJobSuggestionDto[]>({
  endpointKey: "get:/api/processingjobs/suggest/{field}",
  transportMetadata: processingJobControllerSuggestTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["ProcessingJob.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
