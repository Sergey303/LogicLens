// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerOptionsQuery } from "./documentRevisionControllerOptionsQuery.query.generated";
import type { DocumentRevisionOptionDto } from "../documentrevisions/types/DocumentRevisionOptionDto.generated";

export function useDocumentRevisionControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<DocumentRevisionOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentRevisionControllerOptionsQuery, input, options);
}
