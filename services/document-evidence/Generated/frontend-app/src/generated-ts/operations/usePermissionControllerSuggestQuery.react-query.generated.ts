// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { permissionControllerSuggestQuery } from "./permissionControllerSuggestQuery.query.generated";
import type { PermissionSuggestionDto } from "../permissions/types/PermissionSuggestionDto.generated";
import type { SuggestPermissionRequest } from "../permissions/types/SuggestPermissionRequest.generated";

export function usePermissionControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestPermissionRequest; }>,
  options?: GeneratedQueryOptions<PermissionSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(permissionControllerSuggestQuery, input, options);
}
