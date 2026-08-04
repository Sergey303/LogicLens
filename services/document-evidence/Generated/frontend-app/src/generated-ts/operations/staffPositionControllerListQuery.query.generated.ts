import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionControllerListTransportMetadata } from "./staffPositionControllerListTransport.transport.generated";
import type { ListStaffPositionRequest } from "../staffpositions/types/ListStaffPositionRequest.generated";import type { ListStaffPositionResult } from "../staffpositions/types/ListStaffPositionResult.generated";
export const staffPositionControllerListQuery = defineQueryBinding<{ request: ListStaffPositionRequest; }, ListStaffPositionResult>({
  endpointKey: "get:/api/staffpositions",
  transportMetadata: staffPositionControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
