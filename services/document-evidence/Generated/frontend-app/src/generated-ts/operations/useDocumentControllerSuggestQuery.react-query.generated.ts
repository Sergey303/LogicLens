// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentControllerSuggestQuery } from "./documentControllerSuggestQuery.query.generated";
import type { DocumentSuggestionDto } from "../documents/types/DocumentSuggestionDto.generated";
import type { SuggestDocumentRequest } from "../documents/types/SuggestDocumentRequest.generated";

export function useDocumentControllerSuggestQuery(
  input: GeneratedEndpointInput<{ field: string; request: SuggestDocumentRequest; }>,
  options?: GeneratedQueryOptions<DocumentSuggestionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentControllerSuggestQuery, input, options);
}
