// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { permissionControllerOptionsQuery } from "./permissionControllerOptionsQuery.query.generated";
import type { PermissionOptionDto } from "../permissions/types/PermissionOptionDto.generated";

export function usePermissionControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<PermissionOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(permissionControllerOptionsQuery, input, options);
}
