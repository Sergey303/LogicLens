// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentControllerUpdateMutation } from "./documentControllerUpdateMutation.mutation.generated";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";
import type { UpdateDocumentRequest } from "../documents/types/UpdateDocumentRequest.generated";

export function useDocumentControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateDocumentRequest; }, DocumentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentControllerUpdateMutation, options);
}
