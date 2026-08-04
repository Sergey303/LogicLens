import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerGetTransport.metadata.generated.json";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";
export const documentRevisionControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerGetTransport = defineEndpointTransport<{ id: string; }, DocumentRevisionDto>(documentRevisionControllerGetTransportMetadata);
