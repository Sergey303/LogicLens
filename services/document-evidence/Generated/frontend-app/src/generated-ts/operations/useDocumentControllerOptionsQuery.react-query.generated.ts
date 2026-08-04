// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentControllerOptionsQuery } from "./documentControllerOptionsQuery.query.generated";
import type { DocumentOptionDto } from "../documents/types/DocumentOptionDto.generated";

export function useDocumentControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<DocumentOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentControllerOptionsQuery, input, options);
}
