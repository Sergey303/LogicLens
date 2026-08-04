// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerOptionsQuery } from "./staffPositionRoleControllerOptionsQuery.query.generated";
import type { StaffPositionRoleOptionDto } from "../staffpositionroles/types/StaffPositionRoleOptionDto.generated";

export function useStaffPositionRoleControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<StaffPositionRoleOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionRoleControllerOptionsQuery, input, options);
}
