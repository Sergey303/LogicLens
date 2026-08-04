import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerGetTransport.metadata.generated.json";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";
export const processingJobControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerGetTransport = defineEndpointTransport<{ id: string; }, ProcessingJobDto>(processingJobControllerGetTransportMetadata);
