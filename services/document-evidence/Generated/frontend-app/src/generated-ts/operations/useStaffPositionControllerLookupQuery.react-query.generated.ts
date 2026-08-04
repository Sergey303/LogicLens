// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerLookupQuery } from "./staffPositionControllerLookupQuery.query.generated";
import type { LookupStaffPositionRequest } from "../staffpositions/types/LookupStaffPositionRequest.generated";
import type { StaffPositionLookupDto } from "../staffpositions/types/StaffPositionLookupDto.generated";

export function useStaffPositionControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupStaffPositionRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionControllerLookupQuery, input, options);
}
