// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerDeleteMutation } from "./processingJobControllerDeleteMutation.mutation.generated";

export function useProcessingJobControllerDeleteMutation(
  options?: GeneratedMutationOptions<{ id: string; }, void>,
  _config?: unknown,
) {
  return useGeneratedMutation(processingJobControllerDeleteMutation, options);
}
