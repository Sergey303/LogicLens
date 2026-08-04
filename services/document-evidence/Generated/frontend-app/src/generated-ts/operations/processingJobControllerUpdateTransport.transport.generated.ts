import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerUpdateTransport.metadata.generated.json";
import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";import type { UpdateProcessingJobRequest } from "../processingjobs/types/UpdateProcessingJobRequest.generated";
export const processingJobControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateProcessingJobRequest; }, ProcessingJobDto>(processingJobControllerUpdateTransportMetadata);
