// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionAssignmentControllerLookupQuery } from "./staffPositionAssignmentControllerLookupQuery.query.generated";
import type { LookupStaffPositionAssignmentRequest } from "../staffpositionassignments/types/LookupStaffPositionAssignmentRequest.generated";
import type { StaffPositionAssignmentLookupDto } from "../staffpositionassignments/types/StaffPositionAssignmentLookupDto.generated";

export function useStaffPositionAssignmentControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupStaffPositionAssignmentRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionAssignmentLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionAssignmentControllerLookupQuery, input, options);
}
