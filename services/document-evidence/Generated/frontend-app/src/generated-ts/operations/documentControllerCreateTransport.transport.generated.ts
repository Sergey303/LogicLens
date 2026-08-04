import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerCreateTransport.metadata.generated.json";
import type { CreateDocumentRequest } from "../documents/types/CreateDocumentRequest.generated";import type { DocumentDto } from "../documents/types/DocumentDto.generated";
export const documentControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerCreateTransport = defineEndpointTransport<CreateDocumentRequest, DocumentDto>(documentControllerCreateTransportMetadata);
