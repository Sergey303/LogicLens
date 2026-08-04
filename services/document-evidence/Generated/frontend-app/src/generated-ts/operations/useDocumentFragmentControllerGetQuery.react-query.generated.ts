// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerGetQuery } from "./documentFragmentControllerGetQuery.query.generated";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";

export function useDocumentFragmentControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<DocumentFragmentDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentFragmentControllerGetQuery, input, options);
}
