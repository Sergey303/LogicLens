// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerOptionsQuery } from "./staffPositionAssignmentControllerOptionsQuery.query.generated";
import type { StaffPositionAssignmentOptionDto } from "../staffpositionassignments/types/StaffPositionAssignmentOptionDto.generated";

export function useStaffPositionAssignmentControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<StaffPositionAssignmentOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionAssignmentControllerOptionsQuery, input, options);
}
