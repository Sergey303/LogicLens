// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerLookupQuery } from "./storedObjectControllerLookupQuery.query.generated";
import type { LookupStoredObjectRequest } from "../storedobjects/types/LookupStoredObjectRequest.generated";
import type { StoredObjectLookupDto } from "../storedobjects/types/StoredObjectLookupDto.generated";

export function useStoredObjectControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupStoredObjectRequest; }>,
  options?: GeneratedQueryOptions<StoredObjectLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(storedObjectControllerLookupQuery, input, options);
}
