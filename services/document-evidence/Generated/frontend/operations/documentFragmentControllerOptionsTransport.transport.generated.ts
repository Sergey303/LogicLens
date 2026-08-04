import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerOptionsTransport.metadata.generated.json";
import type { DocumentFragmentOptionDto } from "../documentfragments/types/DocumentFragmentOptionDto.generated";
export const documentFragmentControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerOptionsTransport = defineEndpointTransport<{ field: string; }, DocumentFragmentOptionDto[]>(documentFragmentControllerOptionsTransportMetadata);
