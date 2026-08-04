// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerListQuery } from "./storedObjectControllerListQuery.query.generated";
import type { ListStoredObjectRequest } from "../storedobjects/types/ListStoredObjectRequest.generated";
import type { ListStoredObjectResult } from "../storedobjects/types/ListStoredObjectResult.generated";

export function useStoredObjectControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListStoredObjectRequest; }>,
  options?: GeneratedQueryOptions<ListStoredObjectResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(storedObjectControllerListQuery, input, options);
}
