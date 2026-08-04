import { defineQueryBinding } from "../runtime/queryRuntime";
import { documentFragmentControllerOptionsTransportMetadata } from "./documentFragmentControllerOptionsTransport.transport.generated";
import type { DocumentFragmentOptionDto } from "../documentfragments/types/DocumentFragmentOptionDto.generated";
export const documentFragmentControllerOptionsQuery = defineQueryBinding<{ field: string; }, DocumentFragmentOptionDto[]>({
  endpointKey: "get:/api/documentfragments/options/{field}",
  transportMetadata: documentFragmentControllerOptionsTransportMetadata,
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["DocumentFragment.Read"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: [],
});
