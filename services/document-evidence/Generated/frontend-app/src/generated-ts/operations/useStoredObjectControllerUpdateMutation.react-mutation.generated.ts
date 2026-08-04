// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerUpdateMutation } from "./storedObjectControllerUpdateMutation.mutation.generated";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";
import type { UpdateStoredObjectRequest } from "../storedobjects/types/UpdateStoredObjectRequest.generated";

export function useStoredObjectControllerUpdateMutation(
  options?: GeneratedMutationOptions<{ id: string; body: UpdateStoredObjectRequest; }, StoredObjectDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(storedObjectControllerUpdateMutation, options);
}
