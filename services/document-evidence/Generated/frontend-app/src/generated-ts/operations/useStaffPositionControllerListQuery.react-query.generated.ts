// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerListQuery } from "./staffPositionControllerListQuery.query.generated";
import type { ListStaffPositionRequest } from "../staffpositions/types/ListStaffPositionRequest.generated";
import type { ListStaffPositionResult } from "../staffpositions/types/ListStaffPositionResult.generated";

export function useStaffPositionControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListStaffPositionRequest; }>,
  options?: GeneratedQueryOptions<ListStaffPositionResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionControllerListQuery, input, options);
}
