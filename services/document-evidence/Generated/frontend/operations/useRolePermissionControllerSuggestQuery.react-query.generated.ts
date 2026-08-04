// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerSuggestQuery } from "./rolePermissionControllerSuggestQuery.query.generated";
import type { RolePermissionSuggestionDto } from "../rolepermissions/types/RolePermissionSuggestionDto.generated";
import type { SuggestRolePermissionRequest } from "../rolepermissions/types/SuggestRolePermissionRequest.generated";

export function useRolePermissionControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestRolePermissionRequest; }>,
  options?: GeneratedQueryOptions<RolePermissionSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(rolePermissionControllerSuggestQuery, input, options);
}
