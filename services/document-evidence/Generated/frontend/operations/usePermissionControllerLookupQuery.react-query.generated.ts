// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { permissionControllerLookupQuery } from "./permissionControllerLookupQuery.query.generated";
import type { LookupPermissionRequest } from "../permissions/types/LookupPermissionRequest.generated";
import type { PermissionLookupDto } from "../permissions/types/PermissionLookupDto.generated";

export function usePermissionControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupPermissionRequest; }>,
  options?: GeneratedQueryOptions<PermissionLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(permissionControllerLookupQuery, input, options);
}
