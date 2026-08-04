// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentFragmentControllerUpdateMutation } from "./documentFragmentControllerUpdateMutation.mutation.generated";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";
import type { UpdateDocumentFragmentRequest } from "../documentfragments/types/UpdateDocumentFragmentRequest.generated";

export function useDocumentFragmentControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateDocumentFragmentRequest; }, DocumentFragmentDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentFragmentControllerUpdateMutation, options);
}
