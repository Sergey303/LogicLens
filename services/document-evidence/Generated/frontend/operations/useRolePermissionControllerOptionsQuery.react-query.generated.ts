// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerOptionsQuery } from "./rolePermissionControllerOptionsQuery.query.generated";
import type { RolePermissionOptionDto } from "../rolepermissions/types/RolePermissionOptionDto.generated";

export function useRolePermissionControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<RolePermissionOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(rolePermissionControllerOptionsQuery, input, options);
}
