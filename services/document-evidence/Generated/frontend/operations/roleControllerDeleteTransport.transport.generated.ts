import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/roleControllerDeleteTransport.metadata.generated.json";

export const roleControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const roleControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(roleControllerDeleteTransportMetadata);
