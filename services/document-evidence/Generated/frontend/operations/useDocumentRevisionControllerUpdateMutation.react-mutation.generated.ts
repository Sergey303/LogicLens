// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerUpdateMutation } from "./documentRevisionControllerUpdateMutation.mutation.generated";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";
import type { UpdateDocumentRevisionRequest } from "../documentrevisions/types/UpdateDocumentRevisionRequest.generated";

export function useDocumentRevisionControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateDocumentRevisionRequest; }, DocumentRevisionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentRevisionControllerUpdateMutation, options);
}
