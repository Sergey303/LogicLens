// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerListQuery } from "./documentRevisionControllerListQuery.query.generated";
import type { ListDocumentRevisionRequest } from "../documentrevisions/types/ListDocumentRevisionRequest.generated";
import type { ListDocumentRevisionResult } from "../documentrevisions/types/ListDocumentRevisionResult.generated";

export function useDocumentRevisionControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListDocumentRevisionRequest; }>,
  options?: GeneratedQueryOptions<ListDocumentRevisionResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentRevisionControllerListQuery, input, options);
}
