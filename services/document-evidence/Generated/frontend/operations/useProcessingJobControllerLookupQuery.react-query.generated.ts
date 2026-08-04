// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerLookupQuery } from "./processingJobControllerLookupQuery.query.generated";
import type { LookupProcessingJobRequest } from "../processingjobs/types/LookupProcessingJobRequest.generated";
import type { ProcessingJobLookupDto } from "../processingjobs/types/ProcessingJobLookupDto.generated";

export function useProcessingJobControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupProcessingJobRequest; }>,
  options?: GeneratedQueryOptions<ProcessingJobLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(processingJobControllerLookupQuery, input, options);
}
