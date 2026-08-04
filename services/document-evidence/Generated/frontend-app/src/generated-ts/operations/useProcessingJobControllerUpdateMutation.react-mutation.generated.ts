// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerUpdateMutation } from "./processingJobControllerUpdateMutation.mutation.generated";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";
import type { UpdateProcessingJobRequest } from "../processingjobs/types/UpdateProcessingJobRequest.generated";

export function useProcessingJobControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateProcessingJobRequest; }, ProcessingJobDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(processingJobControllerUpdateMutation, options);
}
