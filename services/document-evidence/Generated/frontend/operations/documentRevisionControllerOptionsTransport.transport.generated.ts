import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerOptionsTransport.metadata.generated.json";
import type { DocumentRevisionOptionDto } from "../documentrevisions/types/DocumentRevisionOptionDto.generated";
export const documentRevisionControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerOptionsTransport = defineEndpointTransport<{ field: string; }, DocumentRevisionOptionDto[]>(documentRevisionControllerOptionsTransportMetadata);
