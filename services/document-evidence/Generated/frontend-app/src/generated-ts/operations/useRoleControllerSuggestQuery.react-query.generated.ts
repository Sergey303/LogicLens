// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { roleControllerSuggestQuery } from "./roleControllerSuggestQuery.query.generated";
import type { RoleSuggestionDto } from "../roles/types/RoleSuggestionDto.generated";
import type { SuggestRoleRequest } from "../roles/types/SuggestRoleRequest.generated";

export function useRoleControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestRoleRequest; }>,
  options?: GeneratedQueryOptions<RoleSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(roleControllerSuggestQuery, input, options);
}
