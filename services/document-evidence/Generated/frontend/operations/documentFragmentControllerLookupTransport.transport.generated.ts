import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerLookupTransport.metadata.generated.json";
import type { DocumentFragmentLookupDto } from "../documentfragments/types/DocumentFragmentLookupDto.generated";import type { LookupDocumentFragmentRequest } from "../documentfragments/types/LookupDocumentFragmentRequest.generated";
export const documentFragmentControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerLookupTransport = defineEndpointTransport<{ request: LookupDocumentFragmentRequest; }, DocumentFragmentLookupDto[]>(documentFragmentControllerLookupTransportMetadata);
