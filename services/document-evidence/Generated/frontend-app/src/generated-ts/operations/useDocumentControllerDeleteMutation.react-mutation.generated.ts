// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { documentControllerDeleteMutation } from "./documentControllerDeleteMutation.mutation.generated";

export function useDocumentControllerDeleteMutation(
  options?: GeneratedMutationOptions<{ id: string; }, void>,
  _config?: unknown,
) {
  return useGeneratedMutation(documentControllerDeleteMutation, options);
}
