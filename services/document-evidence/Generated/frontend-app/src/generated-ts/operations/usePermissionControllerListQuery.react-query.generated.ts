// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { permissionControllerListQuery } from "./permissionControllerListQuery.query.generated";
import type { ListPermissionRequest } from "../permissions/types/ListPermissionRequest.generated";
import type { ListPermissionResult } from "../permissions/types/ListPermissionResult.generated";

export function usePermissionControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListPermissionRequest; }>,
  options?: GeneratedQueryOptions<ListPermissionResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(permissionControllerListQuery, input, options);
}
