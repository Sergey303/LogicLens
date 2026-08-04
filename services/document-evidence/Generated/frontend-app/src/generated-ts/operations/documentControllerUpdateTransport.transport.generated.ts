import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerUpdateTransport.metadata.generated.json";
import type { DocumentDto } from "../documents/types/DocumentDto.generated";import type { UpdateDocumentRequest } from "../documents/types/UpdateDocumentRequest.generated";
export const documentControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateDocumentRequest; }, DocumentDto>(documentControllerUpdateTransportMetadata);
