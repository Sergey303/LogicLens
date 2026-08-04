// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerSuggestQuery } from "./processingJobControllerSuggestQuery.query.generated";
import type { ProcessingJobSuggestionDto } from "../processingjobs/types/ProcessingJobSuggestionDto.generated";
import type { SuggestProcessingJobRequest } from "../processingjobs/types/SuggestProcessingJobRequest.generated";

export function useProcessingJobControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestProcessingJobRequest; }>,
  options?: GeneratedQueryOptions<ProcessingJobSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(processingJobControllerSuggestQuery, input, options);
}
