// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerSuggestQuery } from "./documentRevisionControllerSuggestQuery.query.generated";
import type { DocumentRevisionSuggestionDto } from "../documentrevisions/types/DocumentRevisionSuggestionDto.generated";
import type { SuggestDocumentRevisionRequest } from "../documentrevisions/types/SuggestDocumentRevisionRequest.generated";

export function useDocumentRevisionControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestDocumentRevisionRequest; }>,
  options?: GeneratedQueryOptions<DocumentRevisionSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentRevisionControllerSuggestQuery, input, options);
}
