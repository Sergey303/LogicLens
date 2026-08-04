// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentControllerListQuery } from "./documentControllerListQuery.query.generated";
import type { ListDocumentRequest } from "../documents/types/ListDocumentRequest.generated";
import type { ListDocumentResult } from "../documents/types/ListDocumentResult.generated";

export function useDocumentControllerListQuery(
  input: GeneratedEndpointInput<{ request: ListDocumentRequest; }>,
  options?: GeneratedQueryOptions<ListDocumentResult>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentControllerListQuery, input, options);
}
