import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerUpdateTransport.metadata.generated.json";
import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";import type { UpdateDocumentRevisionRequest } from "../documentrevisions/types/UpdateDocumentRevisionRequest.generated";
export const documentRevisionControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateDocumentRevisionRequest; }, DocumentRevisionDto>(documentRevisionControllerUpdateTransportMetadata);
