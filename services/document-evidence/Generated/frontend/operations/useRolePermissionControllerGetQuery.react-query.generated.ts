// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerGetQuery } from "./rolePermissionControllerGetQuery.query.generated";
import type { RolePermissionDto } from "../rolepermissions/types/RolePermissionDto.generated";

export function useRolePermissionControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<RolePermissionDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(rolePermissionControllerGetQuery, input, options);
}
