import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerListTransport.metadata.generated.json";
import type { ListDocumentFragmentRequest } from "../documentfragments/types/ListDocumentFragmentRequest.generated";import type { ListDocumentFragmentResult } from "../documentfragments/types/ListDocumentFragmentResult.generated";
export const documentFragmentControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerListTransport = defineEndpointTransport<{ request: ListDocumentFragmentRequest; }, ListDocumentFragmentResult>(documentFragmentControllerListTransportMetadata);
