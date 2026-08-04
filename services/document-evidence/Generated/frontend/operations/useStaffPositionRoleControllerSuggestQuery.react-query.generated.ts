// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionRoleControllerSuggestQuery } from "./staffPositionRoleControllerSuggestQuery.query.generated";
import type { StaffPositionRoleSuggestionDto } from "../staffpositionroles/types/StaffPositionRoleSuggestionDto.generated";
import type { SuggestStaffPositionRoleRequest } from "../staffpositionroles/types/SuggestStaffPositionRoleRequest.generated";

export function useStaffPositionRoleControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestStaffPositionRoleRequest; }>,
  options?: GeneratedQueryOptions<StaffPositionRoleSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionRoleControllerSuggestQuery, input, options);
}
