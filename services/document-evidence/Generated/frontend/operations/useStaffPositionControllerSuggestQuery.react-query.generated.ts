// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerSuggestQuery } from "./staffPositionControllerSuggestQuery.query.generated";
import type { StaffPositionSuggestionDto } from "../staffpositions/types/StaffPositionSuggestionDto.generated";
import type { SuggestStaffPositionRequest } from "../staffpositions/types/SuggestStaffPositionRequest.generated";

export function useStaffPositionControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestStaffPositionRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionControllerSuggestQuery, input, options);
}
