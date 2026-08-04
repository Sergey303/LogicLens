import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerCreateTransport.metadata.generated.json";
import type { CreateDocumentRevisionRequest } from "../documentrevisions/types/CreateDocumentRevisionRequest.generated";import type { DocumentRevisionDto } from "../documentrevisions/types/DocumentRevisionDto.generated";
export const documentRevisionControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerCreateTransport = defineEndpointTransport<CreateDocumentRevisionRequest, DocumentRevisionDto>(documentRevisionControllerCreateTransportMetadata);
