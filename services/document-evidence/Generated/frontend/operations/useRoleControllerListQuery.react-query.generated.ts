// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { roleControllerListQuery } from "./roleControllerListQuery.query.generated";
import type { ListRoleRequest } from "../roles/types/ListRoleRequest.generated";
import type { ListRoleResult } from "../roles/types/ListRoleResult.generated";

export function useRoleControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListRoleRequest; }>,
  options?: GeneratedQueryOptions<ListRoleResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(roleControllerListQuery, input, options);
}
