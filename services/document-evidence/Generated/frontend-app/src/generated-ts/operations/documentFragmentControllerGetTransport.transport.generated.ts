import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerGetTransport.metadata.generated.json";
import type { DocumentFragmentDto } from "../documentfragments/types/DocumentFragmentDto.generated";
export const documentFragmentControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerGetTransport = defineEndpointTransport<{ id: string; }, DocumentFragmentDto>(documentFragmentControllerGetTransportMetadata);
