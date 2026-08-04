// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerOptionsQuery } from "./documentFragmentControllerOptionsQuery.query.generated";
import type { DocumentFragmentOptionDto } from "../documentfragments/types/DocumentFragmentOptionDto.generated";

export function useDocumentFragmentControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<DocumentFragmentOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentFragmentControllerOptionsQuery, input, options);
}
