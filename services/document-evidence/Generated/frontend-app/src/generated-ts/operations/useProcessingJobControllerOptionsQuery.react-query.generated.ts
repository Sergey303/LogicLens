// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerOptionsQuery } from "./processingJobControllerOptionsQuery.query.generated";
import type { ProcessingJobOptionDto } from "../processingjobs/types/ProcessingJobOptionDto.generated";

export function useProcessingJobControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<ProcessingJobOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(processingJobControllerOptionsQuery, input, options);
}
