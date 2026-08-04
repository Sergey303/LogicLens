// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { roleControllerGetQuery } from "./roleControllerGetQuery.query.generated";
import type { RoleDto } from "../roles/types/RoleDto.generated";

export function useRoleControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<RoleDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(roleControllerGetQuery, input, options);
}
