// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerListQuery } from "./staffPositionRoleControllerListQuery.query.generated";
import type { ListStaffPositionRoleRequest } from "../staffpositionroles/types/ListStaffPositionRoleRequest.generated";
import type { ListStaffPositionRoleResult } from "../staffpositionroles/types/ListStaffPositionRoleResult.generated";

export function useStaffPositionRoleControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListStaffPositionRoleRequest; }>,
  options?: GeneratedQueryOptions<ListStaffPositionRoleResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionRoleControllerListQuery, input, options);
}
