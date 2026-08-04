// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { roleControllerOptionsQuery } from "./roleControllerOptionsQuery.query.generated";
import type { RoleOptionDto } from "../roles/types/RoleOptionDto.generated";

export function useRoleControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<RoleOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(roleControllerOptionsQuery, input, options);
}
