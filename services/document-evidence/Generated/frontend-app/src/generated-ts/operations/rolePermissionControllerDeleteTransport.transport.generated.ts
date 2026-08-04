import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/rolePermissionControllerDeleteTransport.metadata.generated.json";

export const rolePermissionControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const rolePermissionControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(rolePermissionControllerDeleteTransportMetadata);
