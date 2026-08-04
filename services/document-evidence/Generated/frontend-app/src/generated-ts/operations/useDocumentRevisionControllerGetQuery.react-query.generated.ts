// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerGetQuery } from "./documentRevisionControllerGetQuery.query.generated";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";

export function useDocumentRevisionControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<DocumentRevisionDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentRevisionControllerGetQuery, input, options);
}
