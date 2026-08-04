import { defineQueryBinding } from "../runtime/queryRuntime";
import { staffPositionControllerLookupTransportMetadata } from "./staffPositionControllerLookupTransport.transport.generated";
import type { LookupStaffPositionRequest } from "../staffpositions/types/LookupStaffPositionRequest.generated";import type { StaffPositionLookupDto } from "../staffpositions/types/StaffPositionLookupDto.generated";
export const staffPositionControllerLookupQuery = defineQueryBinding<{ request: LookupStaffPositionRequest; }, StaffPositionLookupDto[]>({
  endpointKey: "get:/api/staffpositions/lookup",
  transportMetadata: staffPositionControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["StaffPosition.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
