// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentRevisionControllerCreateMutation } from "./documentRevisionControllerCreateMutation.mutation.generated";
import type { CreateDocumentRevisionRequest } from "../documentrevisions/types/CreateDocumentRevisionRequest.generated";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";

export function useDocumentRevisionControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateDocumentRevisionRequest, DocumentRevisionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentRevisionControllerCreateMutation, options);
}
