// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerGetQuery } from "./processingJobControllerGetQuery.query.generated";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";

export function useProcessingJobControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<ProcessingJobDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(processingJobControllerGetQuery, input, options);
}
