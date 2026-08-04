import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentFragmentControllerGetTransportMetadata } from "./documentFragmentControllerGetTransport.transport.generated";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";
export const documentFragmentControllerGetQuery = defineQueryBinding<{ id: string; }, DocumentFragmentDto>({
  endpointKey: "get:/api/documentfragments/{id}",
  transportMetadata: documentFragmentControllerGetTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["document.fragment.not_found"],
});
