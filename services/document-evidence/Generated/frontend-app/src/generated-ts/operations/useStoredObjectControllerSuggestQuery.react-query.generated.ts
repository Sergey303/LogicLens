// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerSuggestQuery } from "./storedObjectControllerSuggestQuery.query.generated";
import type { StoredObjectSuggestionDto } from "../storedobjects/types/StoredObjectSuggestionDto.generated";
import type { SuggestStoredObjectRequest } from "../storedobjects/types/SuggestStoredObjectRequest.generated";

export function useStoredObjectControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestStoredObjectRequest; }>,
  options?: GeneratedQueryOptions<StoredObjectSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(storedObjectControllerSuggestQuery, input, options);
}
