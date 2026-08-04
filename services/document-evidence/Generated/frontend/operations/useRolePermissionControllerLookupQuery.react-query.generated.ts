// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { rolePermissionControllerLookupQuery } from "./rolePermissionControllerLookupQuery.query.generated";
import type { LookupRolePermissionRequest } from "../rolepermissions/types/LookupRolePermissionRequest.generated";
import type { RolePermissionLookupDto } from "../rolepermissions/types/RolePermissionLookupDto.generated";

export function useRolePermissionControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupRolePermissionRequest; }>,
  options?: GeneratedQueryOptions<RolePermissionLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(rolePermissionControllerLookupQuery, input, options);
}
