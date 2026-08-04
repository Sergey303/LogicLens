import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerDeleteTransport.metadata.generated.json";

export const documentRevisionControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(documentRevisionControllerDeleteTransportMetadata);
