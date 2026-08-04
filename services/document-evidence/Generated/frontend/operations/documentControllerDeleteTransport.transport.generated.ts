import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerDeleteTransport.metadata.generated.json";

export const documentControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(documentControllerDeleteTransportMetadata);
