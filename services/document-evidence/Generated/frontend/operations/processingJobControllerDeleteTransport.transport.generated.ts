import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerDeleteTransport.metadata.generated.json";

export const processingJobControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(processingJobControllerDeleteTransportMetadata);
