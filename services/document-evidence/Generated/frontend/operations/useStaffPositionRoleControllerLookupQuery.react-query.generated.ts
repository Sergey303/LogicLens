// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerLookupQuery } from "./staffPositionRoleControllerLookupQuery.query.generated";
import type { LookupStaffPositionRoleRequest } from "../staffpositionroles/types/LookupStaffPositionRoleRequest.generated";
import type { StaffPositionRoleLookupDto } from "../staffpositionroles/types/StaffPositionRoleLookupDto.generated";

export function useStaffPositionRoleControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupStaffPositionRoleRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionRoleLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionRoleControllerLookupQuery, input, options);
}
