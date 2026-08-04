import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentFragmentControllerLookupTransportMetadata } from "./documentFragmentControllerLookupTransport.transport.generated";
import type { DocumentFragmentLookupDto } from "../documentfragments/types/DocumentFragmentLookupDto.generated";import type { LookupDocumentFragmentRequest } from "../documentfragments/types/LookupDocumentFragmentRequest.generated";
export const documentFragmentControllerLookupQuery = defineQueryBinding<{ request: LookupDocumentFragmentRequest; }, DocumentFragmentLookupDto[]>({
  endpointKey: "get:/api/documentfragments/lookup",
  transportMetadata: documentFragmentControllerLookupTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
