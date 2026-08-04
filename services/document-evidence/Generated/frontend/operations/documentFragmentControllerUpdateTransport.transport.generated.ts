import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerUpdateTransport.metadata.generated.json";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";import type { UpdateDocumentFragmentRequest } from "../documentfragments/types/UpdateDocumentFragmentRequest.generated";
export const documentFragmentControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateDocumentFragmentRequest; }, DocumentFragmentDto>(documentFragmentControllerUpdateTransportMetadata);
