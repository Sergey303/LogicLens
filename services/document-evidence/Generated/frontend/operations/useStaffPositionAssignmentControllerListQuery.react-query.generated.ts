// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerListQuery } from "./staffPositionAssignmentControllerListQuery.query.generated";
import type { ListStaffPositionAssignmentRequest } from "../staffpositionassignments/types/ListStaffPositionAssignmentRequest.generated";
import type { ListStaffPositionAssignmentResult } from "../staffpositionassignments/types/ListStaffPositionAssignmentResult.generated";

export function useStaffPositionAssignmentControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListStaffPositionAssignmentRequest; }>,
  options?: GeneratedQueryOptions<ListStaffPositionAssignmentResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionAssignmentControllerListQuery, input, options);
}
