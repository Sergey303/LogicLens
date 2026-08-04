// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { documentControllerGetQuery } from "./documentControllerGetQuery.query.generated";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";

export function useDocumentControllerGetQuery(
  input: GeneratedEndpointInput<{ id: string; }>,
  options?: GeneratedQueryOptions<DocumentDto>,
  _config?: unknown,
) {
  return useGeneratedQuery(documentControllerGetQuery, input, options);
}
