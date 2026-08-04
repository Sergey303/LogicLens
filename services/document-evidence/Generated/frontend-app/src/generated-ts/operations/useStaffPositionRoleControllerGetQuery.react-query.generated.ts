// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerGetQuery } from "./staffPositionRoleControllerGetQuery.query.generated";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";

export function useStaffPositionRoleControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<StaffPositionRoleDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionRoleControllerGetQuery, input, options);
}
