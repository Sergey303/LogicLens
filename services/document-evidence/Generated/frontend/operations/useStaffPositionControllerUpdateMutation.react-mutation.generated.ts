// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerUpdateMutation } from "./staffPositionControllerUpdateMutation.mutation.generated";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";
import type { UpdateStaffPositionRequest } from "../staffpositions/types/UpdateStaffPositionRequest.generated";

export function useStaffPositionControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateStaffPositionRequest; }, StaffPositionDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(staffPositionControllerUpdateMutation, options);
}
