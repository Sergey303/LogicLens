// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerGetQuery } from "./staffPositionAssignmentControllerGetQuery.query.generated";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";

export function useStaffPositionAssignmentControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<StaffPositionAssignmentDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionAssignmentControllerGetQuery, input, options);
}
