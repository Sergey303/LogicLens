// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentControllerCreateMutation } from "./documentControllerCreateMutation.mutation.generated";
import type { CreateDocumentRequest } from "../documents/types/CreateDocumentRequest.generated";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";

export function useDocumentControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateDocumentRequest, DocumentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentControllerCreateMutation, options);
}
