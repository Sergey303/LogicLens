// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerGetQuery } from "./storedObjectControllerGetQuery.query.generated";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";

export function useStoredObjectControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<StoredObjectDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(storedObjectControllerGetQuery, input, options);
}
