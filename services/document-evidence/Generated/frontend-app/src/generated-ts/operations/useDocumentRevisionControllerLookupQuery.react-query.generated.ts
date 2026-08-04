// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerLookupQuery } from "./documentRevisionControllerLookupQuery.query.generated";
import type { DocumentRevisionLookupDto } from "../documentrevisions/types/DocumentRevisionLookupDto.generated";
import type { LookupDocumentRevisionRequest } from "../documentrevisions/types/LookupDocumentRevisionRequest.generated";

export function useDocumentRevisionControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupDocumentRevisionRequest; }>,
  options?: GeneratedQueryOptions<DocumentRevisionLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentRevisionControllerLookupQuery, input, options);
}
