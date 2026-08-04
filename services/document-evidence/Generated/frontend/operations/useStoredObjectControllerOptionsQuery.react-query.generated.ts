// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerOptionsQuery } from "./storedObjectControllerOptionsQuery.query.generated";
import type { StoredObjectOptionDto } from "../storedobjects/types/StoredObjectOptionDto.generated";

export function useStoredObjectControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<StoredObjectOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(storedObjectControllerOptionsQuery, input, options);
}
