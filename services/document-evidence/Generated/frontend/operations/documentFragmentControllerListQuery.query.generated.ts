import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentFragmentControllerListTransportMetadata } from "./documentFragmentControllerListTransport.transport.generated";
import type { ListDocumentFragmentRequest } from "../documentfragments/types/ListDocumentFragmentRequest.generated";import type { ListDocumentFragmentResult } from "../documentfragments/types/ListDocumentFragmentResult.generated";
export const documentFragmentControllerListQuery = defineQueryBinding<{ request: ListDocumentFragmentRequest; }, ListDocumentFragmentResult>({
  endpointKey: "get:/api/documentfragments",
  transportMetadata: documentFragmentControllerListTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
