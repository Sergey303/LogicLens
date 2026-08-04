// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerListQuery } from "./documentFragmentControllerListQuery.query.generated";
import type { ListDocumentFragmentRequest } from "../documentfragments/types/ListDocumentFragmentRequest.generated";
import type { ListDocumentFragmentResult } from "../documentfragments/types/ListDocumentFragmentResult.generated";

export function useDocumentFragmentControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListDocumentFragmentRequest; }>,
  options?: GeneratedQueryOptions<ListDocumentFragmentResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentFragmentControllerListQuery, input, options);
}
