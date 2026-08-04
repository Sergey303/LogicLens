import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/permissionControllerDeleteTransport.metadata.generated.json";

export const permissionControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const permissionControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(permissionControllerDeleteTransportMetadata);
