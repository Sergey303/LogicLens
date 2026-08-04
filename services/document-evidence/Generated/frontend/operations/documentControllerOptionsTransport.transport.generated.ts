import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerOptionsTransport.metadata.generated.json";
import type { DocumentOptionDto } from "../documents/types/DocumentOptionDto.generated";
export const documentControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerOptionsTransport = defineEndpointTransport<{ field: string; }, DocumentOptionDto[]>(documentControllerOptionsTransportMetadata);
