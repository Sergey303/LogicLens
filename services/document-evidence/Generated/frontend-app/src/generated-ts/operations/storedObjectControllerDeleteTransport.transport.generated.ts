import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerDeleteTransport.metadata.generated.json";

export const storedObjectControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(storedObjectControllerDeleteTransportMetadata);
