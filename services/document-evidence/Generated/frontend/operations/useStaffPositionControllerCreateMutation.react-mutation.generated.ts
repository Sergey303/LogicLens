// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerCreateMutation } from "./staffPositionControllerCreateMutation.mutation.generated";
import type { CreateStaffPositionRequest } from "../staffpositions/types/CreateStaffPositionRequest.generated";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";

export function useStaffPositionControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateStaffPositionRequest, StaffPositionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionControllerCreateMutation, options);
}
