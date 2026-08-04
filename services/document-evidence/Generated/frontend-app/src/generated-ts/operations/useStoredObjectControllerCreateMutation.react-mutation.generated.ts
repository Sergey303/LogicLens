// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useGeneratedMutation } from "../runtime/reactQueryRuntime";
import type { GeneratedMutationOptions } from "../runtime/reactQueryTypes";
import { storedObjectControllerCreateMutation } from "./storedObjectControllerCreateMutation.mutation.generated";
import type { CreateStoredObjectRequest } from "../storedobjects/types/CreateStoredObjectRequest.generated";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";

export function useStoredObjectControllerCreateMutation(
  options?: GeneratedMutationOptions<CreateStoredObjectRequest, StoredObjectDto>,
  _config?: unknown,
) {
  return useGeneratedMutation(storedObjectControllerCreateMutation, options);
}
