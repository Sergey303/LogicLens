// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentControllerLookupQuery } from "./documentControllerLookupQuery.query.generated";
import type { DocumentLookupDto } from "../documents/types/DocumentLookupDto.generated";
import type { LookupDocumentRequest } from "../documents/types/LookupDocumentRequest.generated";

export function useDocumentControllerLookupQuery(
  input: GeneratedEndpointInput<{ request: LookupDocumentRequest; }>,
  options?: GeneratedQueryOptions<DocumentLookupDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentControllerLookupQuery, input, options);
}
