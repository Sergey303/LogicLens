// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedQuery } from "../runtime/reactQueryRuntime";
import type { GeneratedEndpointInput, GeneratedQueryOptions } from "../runtime/reactQueryTypes";
import { staffPositionControllerOptionsQuery } from "./staffPositionControllerOptionsQuery.query.generated";
import type { StaffPositionOptionDto } from "../staffpositions/types/StaffPositionOptionDto.generated";

export function useStaffPositionControllerOptionsQuery(
  input: GeneratedEndpointInput<{ field: string; }>,
  options?: GeneratedQueryOptions<StaffPositionOptionDto[]>,
  _config?: unknown,
) {
  return useGeneratedQuery(staffPositionControllerOptionsQuery, input, options);
}
