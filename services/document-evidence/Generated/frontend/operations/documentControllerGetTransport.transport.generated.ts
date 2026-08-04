import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerGetTransport.metadata.generated.json";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";
export const documentControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerGetTransport = defineEndpointTransport<{ id: string; }, DocumentDto>(documentControllerGetTransportMetadata);
