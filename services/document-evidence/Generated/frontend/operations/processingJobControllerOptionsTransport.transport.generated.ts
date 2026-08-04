import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerOptionsTransport.metadata.generated.json";
import type { ProcessingJobOptionDto } from "../processingjobs/types/ProcessingJobOptionDto.generated";
export const processingJobControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerOptionsTransport = defineEndpointTransport<{ field: string; }, ProcessingJobOptionDto[]>(processingJobControllerOptionsTransportMetadata);
