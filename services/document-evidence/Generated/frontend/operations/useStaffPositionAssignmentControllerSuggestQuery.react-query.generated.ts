// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerSuggestQuery } from "./staffPositionAssignmentControllerSuggestQuery.query.generated";
import type { StaffPositionAssignmentSuggestionDto } from "../staffpositionassignments/types/StaffPositionAssignmentSuggestionDto.generated";
import type { SuggestStaffPositionAssignmentRequest } from "../staffpositionassignments/types/SuggestStaffPositionAssignmentRequest.generated";

export function useStaffPositionAssignmentControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestStaffPositionAssignmentRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionAssignmentSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionAssignmentControllerSuggestQuery, input, options);
}
