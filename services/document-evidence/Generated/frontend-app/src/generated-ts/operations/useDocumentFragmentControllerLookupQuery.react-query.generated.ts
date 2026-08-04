// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerLookupQuery } from "./documentFragmentControllerLookupQuery.query.generated";
import type { DocumentFragmentLookupDto } from "../documentfragments/types/DocumentFragmentLookupDto.generated";
import type { LookupDocumentFragmentRequest } from "../documentfragments/types/LookupDocumentFragmentRequest.generated";

export function useDocumentFragmentControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupDocumentFragmentRequest; }>,
  options?: GeneratedQueryOptions<DocumentFragmentLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentFragmentControllerLookupQuery, input, options);
}
