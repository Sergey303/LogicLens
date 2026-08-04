// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerCreateMutation } from "./documentFragmentControllerCreateMutation.mutation.generated";
import type { CreateDocumentFragmentRequest } from "../documentfragments/types/CreateDocumentFragmentRequest.generated";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";

export function useDocumentFragmentControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateDocumentFragmentRequest, DocumentFragmentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentFragmentControllerCreateMutation, options);
}
