import { defineMutationBinding } from "../runtime/mutationRuntime";
import { permissionControllerDeleteTransportMetadata } from "./permissionControllerDeleteTransport.transport.generated";

export const permissionControllerDeleteMutation = defineMutationBinding<{ id: string; }, void>({
  endpointKey: "delete:/api/permissions/{id}",
  transportMetadata: permissionControllerDeleteTransportMetadata,
  invalidatesEndpointKeys: ["get:/api/permissions", "get:/api/permissions/lookup", "get:/api/permissions/options/{field}", "get:/api/permissions/suggest/{field}", "get:/api/permissions/{id}"],
  realtimeLinks: [],
  availability: {"featureKeys": [], "policyKeys": ["Permission.Delete"], "capabilityKeys": [], "providerKeys": [], "environmentScopes": [], "disabledReasonKey": null},
  errorRefs: ["permission.not_found"],
});
