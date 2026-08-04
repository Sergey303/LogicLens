// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerSuggestQuery } from "./documentFragmentControllerSuggestQuery.query.generated";
import type { DocumentFragmentSuggestionDto } from "../documentfragments/types/DocumentFragmentSuggestionDto.generated";
import type { SuggestDocumentFragmentRequest } from "../documentfragments/types/SuggestDocumentFragmentRequest.generated";

export function useDocumentFragmentControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestDocumentFragmentRequest; }>,
  options?: GeneratedQueryOptions<DocumentFragmentSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentFragmentControllerSuggestQuery, input, options);
}
