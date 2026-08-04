// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { processingJobControllerCreateMutation } from "./processingJobControllerCreateMutation.mutation.generated";
import type { CreateProcessingJobRequest } from "../processingjobs/types/CreateProcessingJobRequest.generated";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";

export function useProcessingJobControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateProcessingJobRequest, ProcessingJobDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(processingJobControllerCreateMutation, options);
}
