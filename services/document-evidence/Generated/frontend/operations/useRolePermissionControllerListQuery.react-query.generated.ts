// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerListQuery } from "./rolePermissionControllerListQuery.query.generated";
import type { ListRolePermissionRequest } from "../rolepermissions/types/ListRolePermissionRequest.generated";
import type { ListRolePermissionResult } from "../rolepermissions/types/ListRolePermissionResult.generated";

export function useRolePermissionControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListRolePermissionRequest; }>,
  options?: GeneratedQueryOptions<ListRolePermissionResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(rolePermissionControllerListQuery, input, options);
}
