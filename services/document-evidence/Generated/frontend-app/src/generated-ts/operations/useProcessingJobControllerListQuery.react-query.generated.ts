// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerListQuery } from "./processingJobControllerListQuery.query.generated";
import type { ListProcessingJobRequest } from "../processingjobs/types/ListProcessingJobRequest.generated";
import type { ListProcessingJobResult } from "../processingjobs/types/ListProcessingJobResult.generated";

export function useProcessingJobControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListProcessingJobRequest; }>,
  options?: GeneratedQueryOptions<ListProcessingJobResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(processingJobControllerListQuery, input, options);
}
