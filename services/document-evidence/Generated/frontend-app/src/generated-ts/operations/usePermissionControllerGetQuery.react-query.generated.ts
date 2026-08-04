// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { permissionControllerGetQuery } from "./permissionControllerGetQuery.query.generated";
import type { PermissionDto } from "../permissions/types/PermissionDto.generated";

export function usePermissionControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<PermissionDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(permissionControllerGetQuery, input, options);
}
