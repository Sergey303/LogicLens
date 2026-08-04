// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { roleControllerLookupQuery } from "./roleControllerLookupQuery.query.generated";
import type { LookupRoleRequest } from "../roles/types/LookupRoleRequest.generated";
import type { RoleLookupDto } from "../roles/types/RoleLookupDto.generated";

export function useRoleControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupRoleRequest; }>,
  options?: GeneratedQueryOptions<RoleLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(roleControllerLookupQuery, input, options);
}
