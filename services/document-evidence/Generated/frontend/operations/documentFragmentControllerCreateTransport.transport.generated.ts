import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerCreateTransport.metadata.generated.json";
import type { CreateDocumentFragmentRequest } from "../documentfragments/types/CreateDocumentFragmentRequest.generated";import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";
export const documentFragmentControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerCreateTransport = defineEndpointTransport<CreateDocumentFragmentRequest, DocumentFragmentDto>(documentFragmentControllerCreateTransportMetadata);
